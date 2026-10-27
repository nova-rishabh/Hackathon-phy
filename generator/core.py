"""Synthetic electoral roll generator: v1 -> v2 churn, context tables, plantings, answer key."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import random
import re
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from .names import DEV_OPS, FEMALE, LAT_OPS, MALE, SURNAME

N_BOOTHS = 100
P_START = "2025-11-01"  # inter-revision period (~1 year)
DEATH_RATE = 6.8 / 1000
MIGRATION_RATE = 0.03
DEATH_REG_RATE = 0.80
ADD_RATE = 0.03
DUP_RATE = 0.005
BENIGN_TYPES = {"hostel_moveout", "boundary_change", "mass_death"}
ANOMALY_TYPES = {"deletion_spike", "addition_spike", "duplicate_cluster", "impossible_age",
                 "oversized_household", "gender_ratio_swing"}
AGES = list(range(18, 96))
AGE_W = [math.exp(-0.031 * (a - 18)) * (1.2 if a < 30 else 1.0) for a in AGES]


def ward_of(b: int) -> str:
    return f"W{(b - 1) // 10 + 1:02d}"


def bid(b: int) -> str:
    return f"B{b:03d}"


def bnum(b: str) -> int:
    return int(b[1:])


def iso(d0: str, rng: random.Random, span: int = 330) -> str:
    return (dt.date.fromisoformat(d0) + dt.timedelta(days=rng.randint(0, span))).isoformat()


class Gen:
    def __init__(self, seed: int, plantings: list[dict]):
        self.rng = random.Random(seed)
        self.plantings = plantings
        self.next_id = 1
        self.v1: list[dict] = []
        self.by_booth: dict[int, list[dict]] = defaultdict(list)
        self.maxhouse: dict[int, int] = {}
        self.death_rows: list[dict] = []
        self.hostel_rows: list[dict] = []
        self.boundary_rows: list[dict] = []
        self.keys: dict[str, dict] = {}
        self.removed_by: dict[str, str] = {}

    # ------------------------------------------------------------ names
    def lat_var(self, text: str) -> str:
        ops = [(a, b) for a, b in LAT_OPS if re.search(a, text, re.I)]
        self.rng.shuffle(ops)
        for a, b in ops:
            def rep(m, b=b):
                return b.capitalize() if m.group(0)[0].isupper() else b
            out = re.sub(a, rep, text, count=1, flags=re.I)
            if out != text:
                return out
        return text

    def dev_var(self, text: str) -> str:
        ops = [(a, b) for a, b in DEV_OPS if a in text]
        if not ops:
            return text
        a, b = self.rng.choice(ops)
        return text.replace(a, b, 1)

    def given(self, gender: str):
        return self.rng.choice(FEMALE if gender == "F" else MALE)

    # ------------------------------------------------------------ records
    def mk(self, b, house, gender, age, sn, gv, rel_type, rel_dev, rel_lat, hh, variant_p=0.10) -> dict:
        name_lat = f"{gv[1]} {sn[1]}"
        name_dev = f"{gv[0]} {sn[0]}"
        shown = self.lat_var(name_lat) if self.rng.random() < variant_p else name_lat
        rshown = self.lat_var(rel_lat) if self.rng.random() < variant_p else rel_lat
        r = dict(vid=f"SBD{self.next_id:07d}", b=b, house=house, name_dev=name_dev, name_lat=shown,
                 canon=name_lat, rel_type=rel_type, rel_dev=rel_dev, rel_lat=rshown, rel_canon=rel_lat,
                 age=age, gender=gender, hh=hh, used=False, tag="")
        self.next_id += 1
        self.v1.append(r)
        self.by_booth[b].append(r)
        self.maxhouse[b] = max(self.maxhouse.get(b, 0), house)
        return r

    def sample_age(self, lo=18, hi=95) -> int:
        while True:
            a = self.rng.choices(AGES, AGE_W)[0]
            if lo <= a <= hi:
                return a

    def household(self, b: int, house: int, k: int | None = None):
        rng = self.rng
        k = k or rng.choices([1, 2, 3, 4, 5, 6, 7, 8], [8, 22, 24, 21, 12, 7, 4, 2])[0]
        sn = rng.choice(SURNAME)
        head_f = rng.random() < 0.12
        head_age = self.sample_age(28, 85)
        fg = self.given("M")
        father = (f"{fg[0]} {sn[0]}", f"{fg[1]} {sn[1]}")
        hg = self.given("F" if head_f else "M")
        head_dev, head_lat = f"{hg[0]} {sn[0]}", f"{hg[1]} {sn[1]}"
        hh = dict(sn=sn, head_dev=head_dev, head_lat=head_lat)
        if head_f:
            self.mk(b, house, "F", head_age, sn, hg, "husband", father[0], father[1], hh)
        else:
            self.mk(b, house, "M", head_age, sn, hg, "father", father[0], father[1], hh)
        n = 1
        if k >= 2 and not head_f:
            g = self.given("F")
            self.mk(b, house, "F", max(18, head_age - rng.randint(0, 8)), sn, g, "husband", head_dev, head_lat, hh)
            n += 1
        while n < k:
            age = head_age - rng.randint(20, 32)
            if age < 18:
                age = self.sample_age(18, 35)
            x = rng.random()
            if x < 0.0008:
                self.mk(b, house, "T", age, sn, self.given("M"), "other", head_dev, head_lat, hh)
            else:
                g = "M" if x < 0.545 else "F"
                self.mk(b, house, g, age, sn, self.given(g), "father", head_dev, head_lat, hh)
            n += 1

    def build_base(self):
        rng = self.rng
        sizes = [min(700, max(300, int(rng.lognormvariate(math.log(500), 0.25)))) for _ in range(N_BOOTHS)]
        scale = 50000 / sum(sizes)
        sizes = [min(700, max(300, int(s * scale))) for s in sizes]
        for i, t in enumerate(sizes):
            b, h = i + 1, 0
            while len(self.by_booth[b]) < t:
                h += 1
                self.household(b, h)

    # ------------------------------------------------------------ helpers
    def pick(self, b: int, n: int, pred=None) -> list[dict]:
        c = [r for r in self.by_booth[b] if not r["used"] and (pred is None or pred(r))]
        got = self.rng.sample(c, min(n, len(c)))
        for r in got:
            r["used"] = True
        return got

    def students(self, b: int, n: int, tag: str):
        rng = self.rng
        house = self.maxhouse[b] + 1
        out = []
        for _ in range(n):
            g = rng.choice(["M", "F"])
            sn, f = rng.choice(SURNAME), rng.choice(SURNAME)
            fg = self.given("M")
            hh = dict(sn=sn, head_dev="", head_lat="")
            r = self.mk(b, house, g, rng.randint(18, 25), sn, self.given(g), "father",
                        f"{fg[0]} {f[0]}", f"{fg[1]} {f[1]}", hh)
            r["used"], r["tag"] = True, tag
            out.append(r)
        return out, house

    def pick_boundary(self, b: int, n: int, to_b: int):
        rng = self.rng
        houses = defaultdict(list)
        for r in self.by_booth[b]:
            if r["tag"] != "hostel" and not r["used"]:
                houses[r["house"]].append(r)
        start = rng.randint(1, max(1, max(houses) - 40))
        moved, hs = [], []
        for h in sorted(houses):
            if h < start:
                continue
            moved += houses[h]
            hs.append(h)
            if len(moved) >= n:
                break
        for r in moved:
            r["used"], r["move_to"] = True, to_b
        return moved, hs

    # ------------------------------------------------------------ plantings (v1 side)
    def apply_v1_plantings(self):
        rng = self.rng
        for p in self.plantings:
            t, b, n = p["type"], bnum(p["booth_id"]), int(p["size"])
            ben = bool(p["is_benign"])
            key = dict(plant_id=p["plant_id"], type=t, is_benign=ben, booth_id=p["booth_id"], voter_ids=[], note="")
            self.keys[p["plant_id"]] = key
            if t == "boundary_change":
                to = p.get("to_booth") or bid(b + 1 if b % 10 else b - 1)
                moved, hs = self.pick_boundary(b, n, bnum(to))
                key["voter_ids"] = [r["vid"] for r in moved]
                key["note"] = f"{len(moved)} records moved {p['booth_id']}->{to}, houses {hs[0]}-{hs[-1]}; listed={ben}"
                if ben:
                    self.boundary_rows.append(dict(change_id=f"BC{len(self.boundary_rows) + 1:02d}",
                        from_booth=p["booth_id"], to_booth=to, house_from=hs[0], house_to=hs[-1],
                        effective_date=iso("2026-05-01", rng, 90)))
            elif t == "hostel_moveout":
                st, house = self.students(b, n, "hostel")
                for r in st:
                    self.removed_by[r["vid"]] = "hostel"
                key["voter_ids"] = [r["vid"] for r in st]
                key["note"] = f"{n} students in house {house} removed in v2; hostel listed={ben}"
                if ben:
                    self.hostel_rows.append(dict(booth_id=p["booth_id"], house_no=house, capacity=n,
                                                 academic_year_end="2026-05-31"))
            elif t == "mass_death":
                vic = self.pick(b, n, lambda r: r["age"] >= 50)
                d0 = dt.date.fromisoformat(iso("2026-02-01", rng, 200))
                for r in vic:
                    self.removed_by[r["vid"]] = "mass_death"
                    if ben:
                        self.death_rows.append(dict(booth_id=p["booth_id"], house_no=r["house"],
                            name_lat=r["canon"], age=r["age"], date=(d0 + dt.timedelta(days=rng.randint(0, 9))).isoformat()))
                key["voter_ids"] = [r["vid"] for r in vic]
                key["note"] = f"{len(vic)} deaths in a short window; registered={ben}"
            elif t == "deletion_spike":
                vic = self.pick(b, n)
                for r in vic:
                    self.removed_by[r["vid"]] = "spike"
                key["voter_ids"] = [r["vid"] for r in vic]
                key["note"] = f"{len(vic)} records removed with no explanatory context"
            elif t == "duplicate_cluster":
                ids = []
                for r in self.pick(b, n):
                    d = self.mk_dup(r)
                    d["used"] = True
                    ids += [r["vid"], d["vid"]]
                key["voter_ids"] = ids
                key["note"] = f"{len(ids) // 2} originals, each with a variant duplicate (new id) kept in v2"
            elif t == "impossible_age":
                vic = self.pick(b, n)
                for r in vic:
                    r["age"] = rng.choice([rng.randint(2, 15), rng.randint(112, 130)])
                key["voter_ids"] = [r["vid"] for r in vic]
                key["note"] = "ages outside 18-110"
            elif t == "oversized_household":
                house = self.maxhouse[b] + 1
                self.household(b, house, n)
                mem = [r for r in self.by_booth[b] if r["house"] == house]
                for r in mem:
                    r["used"] = True
                key["voter_ids"] = [r["vid"] for r in mem]
                key["note"] = f"house {house} holds {len(mem)} electors"
            elif t == "gender_ratio_swing":
                vic = self.pick(b, n, lambda r: r["gender"] == "F")
                for r in vic:
                    r["flip"] = "M"
                key["voter_ids"] = [r["vid"] for r in vic]
                key["note"] = f"{len(vic)} F records recorded as M in v2 (booth gender ratio swing)"
            elif t != "addition_spike":
                raise ValueError(f"unknown planting type {t}")

    def mk_dup(self, r: dict) -> dict:
        rng = self.rng
        b = r["b"]
        house = r["house"] if rng.random() < 0.6 else rng.randint(1, max(1, self.maxhouse[b] - 1))
        d = self.mk(b, house, r["gender"], max(18, r["age"] + rng.choice([-1, 0, 0, 1])), r["hh"]["sn"],
                    ("x", "x"), r["rel_type"], r["rel_dev"], r["rel_canon"], r["hh"], variant_p=0)
        d["name_dev"] = self.dev_var(r["name_dev"])
        d["name_lat"] = self.lat_var(r["canon"])
        d["rel_lat"] = self.lat_var(r["rel_canon"]) if rng.random() < 0.5 else r["rel_canon"]
        d["canon"] = r["canon"]
        d["dup_of"] = r["vid"]
        return d

    def background_context(self):
        rng = self.rng
        taken = {bnum(p["booth_id"]) for p in self.plantings}
        free = [b for b in range(1, N_BOOTHS + 1) if b not in taken]
        for b in rng.sample([x for x in free if len(self.by_booth[x]) <= 560], 4):  # background hostels
            cap = rng.randint(50, 100)
            st, house = self.students(b, cap, "hostel")
            leave = rng.uniform(0.5, 0.7)
            for r in st:
                if rng.random() < leave:
                    self.removed_by[r["vid"]] = "hostel"
            self.hostel_rows.append(dict(booth_id=bid(b), house_no=house, capacity=cap,
                                         academic_year_end="2026-05-31"))
        want = rng.choice([2, 3])  # background boundary changes: top up to 2-3 total
        while len(self.boundary_rows) < want:
            b = rng.choice([x for x in free if x % 10 != 0])
            moved, hs = self.pick_boundary(b, rng.randint(15, 30), b + 1)
            self.boundary_rows.append(dict(change_id=f"BC{len(self.boundary_rows) + 1:02d}",
                from_booth=bid(b), to_booth=bid(b + 1), house_from=hs[0], house_to=hs[-1],
                effective_date=iso("2026-05-01", rng, 90)))
        cand = [r for r in self.v1 if not r["used"]]  # ~0.5% cross-script duplicates, half cleaned in v2
        for r in rng.sample(cand, int(DUP_RATE * len(self.v1))):
            r["used"] = True
            d = self.mk_dup(r)
            d["used"] = True
            if rng.random() < 0.5:
                self.removed_by[d["vid"]] = "dup_cleanup"

    # ------------------------------------------------------------ churn
    @staticmethod
    def death_p(age, k):
        return min(0.4, k * math.exp(0.07 * (age - 18)))

    @staticmethod
    def mig_w(age):
        return 1.6 if age < 36 else (1.0 if age < 61 else 0.5)

    def churn(self):
        rng = self.rng
        pool = [r for r in self.v1 if not r["used"]]
        lo, hi = 1e-7, 1e-2
        for _ in range(60):
            k = (lo + hi) / 2
            tot = sum(self.death_p(r["age"], k) for r in pool) / len(pool)
            lo, hi = (k, hi) if tot < DEATH_RATE else (lo, k)
        self.death_k = k
        self.mig_k = MIGRATION_RATE / (sum(self.mig_w(r["age"]) for r in pool) / len(pool))
        for r in pool:
            if rng.random() < self.death_p(r["age"], k):
                self.removed_by[r["vid"]] = "death"
                if rng.random() < DEATH_REG_RATE:
                    self.death_rows.append(dict(booth_id=bid(r["b"]), house_no=r["house"], name_lat=r["canon"],
                        age=max(0, r["age"] + rng.choice([-1, 0, 0, 0, 1])), date=iso(P_START, rng)))
            elif rng.random() < self.mig_k * self.mig_w(r["age"]):
                self.removed_by[r["vid"]] = "shifted"

    def churn_params(self):
        out = []
        for lo, hi in [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 74), (75, 120)]:
            ages = [r["age"] for r in self.v1 if not r["used"] and lo <= r["age"] <= hi]
            d = sum(self.death_p(a, self.death_k) for a in ages) / len(ages)
            m = sum(self.mig_k * self.mig_w(a) for a in ages) / len(ages)
            out.append(dict(age_lo=lo, age_hi=hi, death_rate=round(d, 5), migration_rate=round(m, 5),
                            p_band=round(d + m, 5)))
        return dict(note="Background removal rate by age band from the generator churn model "
                         "(death: Gompertz-shaped hazard scaled to 6.8/1000; migration ~3%).",
                    death_rate_overall=DEATH_RATE, migration_rate_overall=MIGRATION_RATE, bands=out)

    # ------------------------------------------------------------ v2
    def build_v2(self):
        rng = self.rng
        v2 = []
        for r in self.v1:
            if r["vid"] in self.removed_by:
                continue
            q = dict(r)
            q["age"] += 1
            if "move_to" in r:
                q["b"] = r["move_to"]
            if "flip" in r:
                q["gender"] = r["flip"]
            elif not r["used"] and rng.random() < 0.004:  # spelling correction
                q["name_lat"] = r["canon"] if r["name_lat"] != r["canon"] else self.lat_var(r["canon"])
                if rng.random() < 0.3:
                    q["name_dev"] = self.dev_var(r["name_dev"])
            v2.append(q)

        def add(b, n_new, ages_fn, newhouses=False):
            ids = []
            members = [r for r in self.by_booth[b] if r["hh"]["head_lat"]]
            for i in range(n_new):
                if newhouses:
                    if i % 4 == 0:
                        self.maxhouse[b] += 1
                        sn = rng.choice(SURNAME)
                        hg = self.given("M")
                        hh = dict(sn=sn, head_dev=f"{hg[0]} {sn[0]}", head_lat=f"{hg[1]} {sn[1]}")
                    house = self.maxhouse[b]
                else:
                    m = rng.choice(members)
                    house, hh = m["house"], m["hh"]
                sn = hh["sn"]
                g = "M" if rng.random() < 0.51 else "F"
                gv = self.given(g)
                nm = f"{gv[1]} {sn[1]}"
                r = dict(vid=f"SBD{self.next_id:07d}", b=b, house=house, name_dev=f"{gv[0]} {sn[0]}",
                         name_lat=self.lat_var(nm) if rng.random() < 0.1 else nm, canon=nm,
                         rel_type="father", rel_dev=hh["head_dev"], rel_lat=hh["head_lat"], rel_canon=hh["head_lat"],
                         age=ages_fn(), gender=g, hh=hh, used=False, tag="new")
                self.next_id += 1
                v2.append(r)
                ids.append(r["vid"])
            return ids

        bg_ages = lambda: 18 if rng.random() < 0.7 else rng.randint(20, 45)
        for b in range(1, N_BOOTHS + 1):
            add(b, max(0, round(len(self.by_booth[b]) * ADD_RATE + rng.gauss(0, 1.5))), bg_ages)
        for p in self.plantings:
            if p["type"] == "addition_spike":
                k = self.keys[p["plant_id"]]
                k["voter_ids"] = add(bnum(p["booth_id"]), int(p["size"]), lambda: self.sample_age(18, 70), True)
                k["note"] = f"{len(k['voter_ids'])} new records added to {p['booth_id']} in v2"
        self.v2 = v2

    # ------------------------------------------------------------ output
    def rows(self, recs, ver):
        grouped = defaultdict(list)
        for r in recs:
            grouped[r["b"]].append(r)
        out = []
        for b in sorted(grouped):
            for i, r in enumerate(sorted(grouped[b], key=lambda x: (x["house"], x["vid"])), 1):
                out.append(dict(voter_id=r["vid"], roll_version=ver, ward_id=ward_of(b), booth_id=bid(b),
                    serial_no=i, house_no=str(r["house"]), name_dev=r["name_dev"], name_lat=r["name_lat"],
                    relation_type=r["rel_type"], relation_name_dev=r["rel_dev"], relation_name_lat=r["rel_lat"],
                    age=r["age"], gender=r["gender"]))
        return pd.DataFrame(out)


def write_csv(path: Path, rows: list[dict], cols: list[str]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def auto_plantings(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    sizes = dict(deletion_spike=(30, 60), addition_spike=(30, 60), duplicate_cluster=(8, 20),
                 impossible_age=(3, 8), oversized_household=(16, 22), gender_ratio_swing=(40, 70),
                 hostel_moveout=(40, 90), boundary_change=(40, 90), mass_death=(15, 30))
    types = list(sizes)
    booths = rng.sample([b for b in range(1, N_BOOTHS + 1) if b % 10 != 0], n)
    out = []
    for i, b in enumerate(booths, 1):
        t = types[(i - 1) % len(types)] if i <= len(types) else rng.choice(types)
        lo, hi = sizes[t]
        out.append(dict(plant_id=f"T{i:02d}", type=t, booth_id=bid(b), size=rng.randint(lo, hi),
                        is_benign=t in BENIGN_TYPES))
    return out


def load_config(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    ps = cfg.get("plantings", [])
    for p in ps:
        for k in ("plant_id", "type", "booth_id", "size", "is_benign"):
            if k not in p:
                raise SystemExit(f"planting {p} missing '{k}'")
        if p["type"] not in ANOMALY_TYPES | BENIGN_TYPES:
            raise SystemExit(f"unknown planting type {p['type']}")
    return ps


def run(plantings, seed, out: Path, key_path: Path):
    t0 = time.time()
    from contracts.models import Planting, RollRow
    g = Gen(seed, plantings)
    g.build_base()
    g.apply_v1_plantings()
    g.background_context()
    g.churn()
    g.build_v2()
    d1, d2 = g.rows(g.v1, "v1"), g.rows(g.v2, "v2")
    (out / "context").mkdir(parents=True, exist_ok=True)
    for df, n in ((d1, "roll_v1"), (d2, "roll_v2")):
        df.to_parquet(out / f"{n}.parquet", index=False)
        df.to_csv(out / f"{n}.csv", index=False, encoding="utf-8")
        for rec in df.sample(500, random_state=1).to_dict("records"):
            RollRow(**rec)
    ctx = out / "context"
    write_csv(ctx / "death_register.csv", g.death_rows, ["booth_id", "house_no", "name_lat", "age", "date"])
    write_csv(ctx / "hostel_list.csv", g.hostel_rows, ["booth_id", "house_no", "capacity", "academic_year_end"])
    write_csv(ctx / "boundary_changes.csv", g.boundary_rows,
              ["change_id", "from_booth", "to_booth", "house_from", "house_to", "effective_date"])
    with open(out / "churn_params.json", "w", encoding="utf-8") as f:
        json.dump(g.churn_params(), f, ensure_ascii=False, indent=2)
    key = [Planting(**kk).model_dump() for kk in g.keys.values()]
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=2)
    i1, i2 = set(d1.voter_id), set(d2.voter_id)
    print(f"{out}: v1={len(d1)} v2={len(d2)} deleted={len(i1 - i2)} added={len(i2 - i1)} "
          f"deaths_reg={len(g.death_rows)} hostels={len(g.hostel_rows)} boundaries={len(g.boundary_rows)} "
          f"plantings={len(key)} runtime={time.time() - t0:.1f}s")


def main():
    ap = argparse.ArgumentParser(prog="python -m generator")
    ap.add_argument("--config", help="planting YAML (see generator/README.md)")
    ap.add_argument("--key", help="answer key output path (JSON list of Planting)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="artifacts")
    ap.add_argument("--auto-plant", type=int, default=0, help="random plantings; writes to <out>/training/")
    a = ap.parse_args()
    out = Path(a.out)
    if a.auto_plant:
        out = out / "training"
        out.mkdir(parents=True, exist_ok=True)
        run(auto_plantings(a.auto_plant, a.seed), a.seed, out, Path(a.key) if a.key else out / "answer_key.json")
    else:
        if not a.config or not a.key:
            ap.error("--config and --key are required (or use --auto-plant N)")
        out.mkdir(parents=True, exist_ok=True)
        run(load_config(a.config), a.seed, out, Path(a.key))
