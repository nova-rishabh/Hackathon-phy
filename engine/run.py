"""python -m engine.run [--data artifacts] [--out artifacts] [--train-data artifacts/training --train-key ...]
                      [--workers N] [--bench [--scale 20]]

Writes flags.json (list of contracts Flag), stories.json (list of StoryResult) and aggregates.json (Claim Court
O(1) lookups). --bench also writes bench.json (wall time per stage, duplicate pair counts, optional 1M clone run
and the per-ward parallel speed-up).
The engine never reads private/. The answer key is only read via an explicit CLI path in engine.eval,
or for calibration when the caller passes --train-key (training district only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from contracts.models import Flag, Metrics, Scope, StoryResult

from . import rules
from .confidence import TRAIN_WITH_BENIGN, Calibrator, band_of, feature
from .data import load
from .diff import diff
from .dupes import find_clusters
from .stats import band_rates, booth_tests
from .stories import compute_stories, load_tables

# Flag types the training key cannot label. Background duplicates and relation-conflict side effects are now
# labelled through <key>.background.json (generator), so every type is calibrated.
NO_CALIBRATION: set[str] = set()


@contextmanager
def _stage(timings: dict | None, name: str):
    t = time.perf_counter()
    yield
    if timings is not None:
        timings[name] = round((time.perf_counter() - t) * 1000, 1)


# ------------------------------------------------------------------ per-ward worker (booth-local stages)

def _ward_job(args):
    v1w, v2w = args
    s1, s2 = {}, {}
    t = time.perf_counter()
    c1, c2 = find_clusters(v1w, s1), find_clusters(v2w, s2)
    rc = rules.relation_conflict(v2w)
    return c1, c2, rc, s1, s2, time.perf_counter() - t


def _local_stages(d, workers: int, timings: dict | None):
    """Duplicates (blocks never cross a booth) and relation_conflict (per household) are booth-local, so a
    per-ward split is exact. workers<=1 runs them in-process."""
    if workers <= 1:
        s1, s2 = {}, {}
        with _stage(timings, "duplicates_v1"):
            c1 = find_clusters(d.v1, s1)
        with _stage(timings, "duplicates_v2"):
            c2 = find_clusters(d.v2, s2)
        with _stage(timings, "rule_relation_conflict"):
            rc = rules.relation_conflict(d.v2)
        return c1, c2, rc, s1, s2
    wards = sorted(set(d.v1.ward_id) | set(d.v2.ward_id))
    g1, g2 = dict(tuple(d.v1.groupby("ward_id"))), dict(tuple(d.v2.groupby("ward_id")))
    empty = d.v1.iloc[:0]
    jobs = [(g1.get(w, empty), g2.get(w, empty)) for w in wards]
    c1, c2, rc = [], [], []
    s1 = dict(n=0, candidate_pairs=0, scored_pairs=0, naive_pairs=0, edges=0)
    s2 = dict(s1)
    with _stage(timings, "parallel_local_stages"):
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for a, b, r, x1, x2, _ in ex.map(_ward_job, jobs, chunksize=max(1, len(jobs) // (workers * 4))):
                c1 += a
                c2 += b
                rc += r
                for k in s1:
                    s1[k] += x1.get(k, 0)
                    s2[k] += x2.get(k, 0)
    n1, n2 = len(d.v1), len(d.v2)
    s1["naive_pairs"], s2["naive_pairs"] = n1 * (n1 - 1) // 2, n2 * (n2 - 1) // 2
    return sorted(c1, key=lambda c: c["voter_ids"]), sorted(c2, key=lambda c: c["voter_ids"]), rc, s1, s2


def analyse(data_dir=None, timings: dict | None = None, workers: int = 1, data=None) -> dict:
    with _stage(timings, "load"):
        d = data if data is not None else load(data_dir)
        tables = load_tables(data_dir) if data_dir is not None else {}
    with _stage(timings, "background_rates"):
        rates = band_rates(d.v1, d.v2)
    with _stage(timings, "diff"):
        df = diff(d.v1, d.v2)
    with _stage(timings, "booth_tests"):
        tests = booth_tests(d.v1, d.v2, rates)
    c1, c2, rc, s1, s2 = _local_stages(d, workers, timings)
    with _stage(timings, "stories"):
        stories = compute_stories(d.v1, d.v2, d.death, d.hostel, d.boundary, c1, rates, tables=tables)
    with _stage(timings, "official_parent_gaps"):
        gaps = rules.parent_age_gaps(d.v2)
    return {"parent_gaps": gaps, "data": d, "rates": rates, "diff": df, "tests": tests, "clusters": {"v1": c1, "v2": c2},
            "relation_conflicts": rc, "pair_stats": {"v1": s1, "v2": s2}, "stories": stories}


def _fid(ftype, scope: Scope, metrics: Metrics) -> str:
    ev = json.dumps([scope.model_dump(), metrics.model_dump()], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((ftype + ev).encode("utf-8")).hexdigest()[:12]


def raw_flags(a: dict) -> list[dict]:
    """Flags before calibration: dict(type, scope, metrics, reasons, stories, q, score, benign)."""
    d, df, tests = a["data"], a["diff"], a["tests"]
    out = []
    deleted_by_booth = df["deleted"].groupby("booth_id").voter_id.apply(list).to_dict()
    added_by_booth = df["added"].groupby("booth_id").voter_id.apply(list).to_dict()
    for booth, r in tests.iterrows():
        if r.del_q < 0.05 and r.del_obs > 0:
            st = a["stories"].get(booth)
            out.append(dict(type="deletion_spike", scope=Scope(level="booth", booth_id=booth, voter_ids=deleted_by_booth.get(booth, [])),
                            metrics=Metrics(observed=float(r.del_obs), expected=float(r.del_exp), n=int(r.n_v1),
                                            p_value=float(r.del_p), q_value=float(r.del_q)),
                            # Confidence reads the leftover after the innocent stories, not the raw spike: a spike the
                            # evidence fully explains is not evidence of anything. Cleared unless that leftover is
                            # itself significant ("mixed" booths with a background-level leftover are cleared too).
                            reasons=["DEL_RATE_GT_EXPECTED_BH05"], stories=st,
                            q=float(st.residual.p_value) if st else float(r.del_q),
                            benign=bool(st and st.outcome != "unusual")))
        if r.add_q < 0.05 and r.add_obs > 0:
            out.append(dict(type="addition_spike", scope=Scope(level="booth", booth_id=booth, voter_ids=added_by_booth.get(booth, [])),
                            metrics=Metrics(observed=float(r.add_obs), expected=float(r.add_exp), n=int(r.n_v2),
                                            p_value=float(r.add_p), q_value=float(r.add_q)),
                            reasons=["ADD_RATE_GT_EXPECTED_BH05"], stories=None, q=float(r.add_q)))
    seen = set()
    v2_ids = set(d.v2.voter_id)
    for ver in ("v2", "v1"):
        for c in a["clusters"][ver]:
            key = tuple(c["voter_ids"])
            if key in seen:
                continue
            seen.add(key)
            reasons = ["XSCRIPT_NAME_MATCH", "SAME_RELATION_SAME_HOUSE" if c["house_no"] else "NAME_RELATION_MATCH"]
            if ver == "v1" and not set(key) <= v2_ids:
                reasons.append("MEMBER_REMOVED_IN_V2")
            out.append(dict(type="duplicate_cluster",
                            scope=Scope(level="record", booth_id=c["booth_id"], house_no=c["house_no"], voter_ids=c["voter_ids"]),
                            metrics=Metrics(observed=c["score"], n=len(key), unit="match_score"),
                            reasons=reasons, stories=None, score=c["score"]))
    for x in rules.impossible_age(d.v2):
        out.append(dict(type="impossible_age", scope=Scope(level="record", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=x["age"], n=1, unit="years"), reasons=["AGE_OUT_OF_RANGE_18_110"], stories=None))
    hostels = {(str(r.booth_id), str(r.house_no)) for r in d.hostel.itertuples()}
    for x in rules.oversized_household(d.v2):
        listed = (x["booth_id"], x["house_no"]) in hostels
        out.append(dict(type="oversized_household", scope=Scope(level="household", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=x["size"], expected=15, n=x["size"], unit="electors"),
                        reasons=["HOUSEHOLD_GT_15"] + (["HOUSE_IN_HOSTEL_LIST"] if listed else []), stories=None, benign=listed))
    for x in rules.gender_ratio_swing(d.v1, d.v2):
        out.append(dict(type="gender_ratio_swing", scope=Scope(level="booth", booth_id=x["booth_id"]),
                        metrics=Metrics(observed=abs(x["swing"]), expected=8, n=x["n"], unit="percentage_points"),
                        reasons=["GENDER_SHARE_SWING_GT_8PT"], stories=None))
    for x in a["relation_conflicts"]:
        out.append(dict(type="relation_conflict", scope=Scope(level="household", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=x["pairs"], n=len(x["voter_ids"]), unit="pairs"),
                        reasons=["RELATION_CONFLICT_SAME_HOUSE"] + [w.upper() for w in x["whys"]], stories=None))
    return out


def build_flags(raw: list[dict], cal: Calibrator) -> list[Flag]:
    flags = []
    for r in raw:
        benign = bool(r.get("benign"))
        x = feature(r["type"], r.get("q"), r.get("score"))
        conf, n = cal.predict(r["type"], x, benign)
        flags.append(Flag(flag_id=_fid(r["type"], r["scope"], r["metrics"]), type=r["type"], scope=r["scope"],
                          metrics=r["metrics"], reason_codes=r["reasons"], stories=r["stories"], confidence=conf,
                          confidence_band=band_of(conf), confidence_n=n, likely_benign=benign))
    return sorted(flags, key=lambda f: (f.type, f.scope.booth_id, f.flag_id))


def train_calibrator(train_dir, key_path, workers: int = 1) -> Calibrator:
    """Platt per type on the training district. Flags already judged likely_benign are left out (their confidence
    is scaled separately), and NO_CALIBRATION types keep the documented heuristic."""
    from .eval import load_background, load_key, matches, on_background  # key read only via explicit CLI path
    key = [p for p in load_key(key_path) if not p.is_benign]
    bg = load_background(key_path)
    raw = raw_flags(analyse(train_dir, workers=workers))
    samples: dict = {}
    for r in raw:
        if r["type"] in NO_CALIBRATION or (r.get("benign") and r["type"] not in TRAIN_WITH_BENIGN):
            continue
        f = build_flags([r], Calibrator())[0]
        xs, ys = samples.setdefault(r["type"], ([], []))
        xs.append(feature(r["type"], r.get("q"), r.get("score")))
        ys.append(int(any(matches(f, p) for p in key) or on_background(f, bg)))
    return Calibrator().fit(samples)


def write_outputs(an: dict, flags: list[Flag], out: Path):
    from .aggregates import build_aggregates
    out.mkdir(parents=True, exist_ok=True)
    (out / "flags.json").write_text(json.dumps([f.model_dump(mode="json") for f in flags], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "parent_gaps.json").write_text(json.dumps(an.get("parent_gaps", []), ensure_ascii=False), encoding="utf-8")
    st = [s.model_dump(mode="json", warnings=False) for s in an["stories"].values()]
    try:
        for s in st:
            StoryResult.model_validate(s)
    except Exception as e:  # extra YAML sources outside the contract Literals (S12)
        print(f"warning: stories.json has codes outside contracts StoryCode/context_used: {str(e).splitlines()[0]}")
    (out / "stories.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "aggregates.json").write_text(json.dumps(build_aggregates(an, flags), ensure_ascii=False), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="artifacts")
    ap.add_argument("--out", default="artifacts")
    ap.add_argument("--train-data")
    ap.add_argument("--train-key")
    ap.add_argument("--workers", type=int, default=1, help="processes for the per-ward stages (duplicates, relation rule)")
    ap.add_argument("--bench", action="store_true", help="time every stage and write <out>/bench.json")
    ap.add_argument("--scale", type=int, default=0, help="with --bench: also run a clone of the district x N (20 = ~1M)")
    a = ap.parse_args()
    if a.train_data is None and (Path(a.data) / "training" / "answer_key.json").exists() and a.train_key is None:
        a.train_data, a.train_key = str(Path(a.data) / "training"), str(Path(a.data) / "training" / "answer_key.json")
    if a.bench:
        from .bench import run_bench
        run_bench(a)
        return
    t0 = time.time()
    cal = train_calibrator(a.train_data, a.train_key, a.workers) if a.train_data and a.train_key else Calibrator()
    an = analyse(a.data, workers=a.workers)
    flags = build_flags(raw_flags(an), cal)
    write_outputs(an, flags, Path(a.out))
    by = {}
    for f in flags:
        by[f.type] = by.get(f.type, 0) + 1
    print(f"flags={len(flags)} by_type={by} stories={len(an['stories'])} calibrated={sorted(cal.models)} "
          f"runtime_ms={int((time.time() - t0) * 1000)}")


if __name__ == "__main__":
    main()
