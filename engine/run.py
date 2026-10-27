"""python -m engine.run --data <dir> --out <dir> [--train-data <dir> --train-key <answer_key.json>]

Writes flags.json (list of contracts Flag) and stories.json (list of StoryResult).
The engine never reads private/. The answer key is only read via an explicit CLI path in engine.eval,
or for calibration when the caller passes --train-key (training district only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from contracts.models import Flag, Metrics, Scope, StoryResult

from . import rules
from .confidence import Calibrator, band_of, feature
from .data import load
from .diff import diff
from .dupes import find_clusters
from .stats import band_rates, booth_tests
from .stories import compute_stories


def _fid(ftype, scope: Scope, metrics: Metrics) -> str:
    ev = json.dumps([scope.model_dump(), metrics.model_dump()], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((ftype + ev).encode("utf-8")).hexdigest()[:12]


def analyse(data_dir) -> dict:
    d = load(data_dir)
    rates = band_rates(d.v1, d.v2)
    df = diff(d.v1, d.v2)
    tests = booth_tests(d.v1, d.v2, rates)
    clusters = {"v1": find_clusters(d.v1), "v2": find_clusters(d.v2)}
    stories = compute_stories(d.v1, d.v2, d.death, d.hostel, d.boundary, clusters["v1"], rates)
    return {"data": d, "rates": rates, "diff": df, "tests": tests, "clusters": clusters, "stories": stories}


def raw_flags(a: dict) -> list[dict]:
    """Flags before calibration: dict(type, scope, metrics, reasons, stories, q, score)."""
    d, df, tests = a["data"], a["diff"], a["tests"]
    out = []
    deleted_by_booth = df["deleted"].groupby("booth_id").voter_id.apply(list).to_dict()
    added_by_booth = df["added"].groupby("booth_id").voter_id.apply(list).to_dict()
    for booth, r in tests.iterrows():
        if r.del_q < 0.05 and r.del_obs > 0:
            out.append(dict(type="deletion_spike", scope=Scope(level="booth", booth_id=booth, voter_ids=deleted_by_booth.get(booth, [])),
                            metrics=Metrics(observed=float(r.del_obs), expected=float(r.del_exp), n=int(r.n_v1),
                                            p_value=float(r.del_p), q_value=float(r.del_q)),
                            reasons=["DEL_RATE_GT_EXPECTED_BH05"], stories=a["stories"].get(booth), q=float(r.del_q)))
        if r.add_q < 0.05 and r.add_obs > 0:
            out.append(dict(type="addition_spike", scope=Scope(level="booth", booth_id=booth, voter_ids=added_by_booth.get(booth, [])),
                            metrics=Metrics(observed=float(r.add_obs), expected=float(r.add_exp), n=int(r.n_v2),
                                            p_value=float(r.add_p), q_value=float(r.add_q)),
                            reasons=["ADD_RATE_GT_EXPECTED_BH05"], stories=None, q=float(r.add_q)))
    seen = set()
    for ver in ("v2", "v1"):
        for c in a["clusters"][ver]:
            key = tuple(c["voter_ids"])
            if key in seen:
                continue
            seen.add(key)
            reasons = ["XSCRIPT_NAME_MATCH", "SAME_RELATION_SAME_HOUSE" if c["house_no"] else "NAME_RELATION_MATCH"]
            if ver == "v1" and not set(key) <= set(d.v2.voter_id):
                reasons.append("MEMBER_REMOVED_IN_V2")
            out.append(dict(type="duplicate_cluster",
                            scope=Scope(level="record", booth_id=c["booth_id"], house_no=c["house_no"], voter_ids=c["voter_ids"]),
                            metrics=Metrics(observed=c["score"], n=len(key), unit="match_score"),
                            reasons=reasons, stories=None, score=c["score"]))
    for x in rules.impossible_age(d.v2):
        out.append(dict(type="impossible_age", scope=Scope(level="record", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=x["age"], n=1, unit="years"), reasons=["AGE_OUT_OF_RANGE_18_110"], stories=None))
    for x in rules.oversized_household(d.v2):
        out.append(dict(type="oversized_household", scope=Scope(level="household", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=x["size"], expected=15, n=x["size"], unit="electors"), reasons=["HOUSEHOLD_GT_15"], stories=None))
    for x in rules.gender_ratio_swing(d.v1, d.v2):
        out.append(dict(type="gender_ratio_swing", scope=Scope(level="booth", booth_id=x["booth_id"]),
                        metrics=Metrics(observed=abs(x["swing"]), expected=8, n=x["n"], unit="percentage_points"),
                        reasons=["GENDER_SHARE_SWING_GT_8PT"], stories=None))
    for x in rules.relation_conflict(d.v2):
        out.append(dict(type="relation_conflict", scope=Scope(level="household", booth_id=x["booth_id"], house_no=x["house_no"], voter_ids=x["voter_ids"]),
                        metrics=Metrics(observed=1, n=2, unit="pair"), reasons=["RELATION_CONFLICT_SAME_HOUSE", x["why"].upper()], stories=None))
    return out


def build_flags(raw: list[dict], cal: Calibrator) -> list[Flag]:
    flags = []
    for r in raw:
        benign = bool(r["stories"] and r["stories"].outcome == "likely_benign")
        x = feature(r["type"], r.get("q"), r.get("score"))
        conf, n = cal.predict(r["type"], x, benign)
        flags.append(Flag(flag_id=_fid(r["type"], r["scope"], r["metrics"]), type=r["type"], scope=r["scope"],
                          metrics=r["metrics"], reason_codes=r["reasons"], stories=r["stories"], confidence=conf,
                          confidence_band=band_of(conf), confidence_n=n, likely_benign=benign))
    return sorted(flags, key=lambda f: (f.type, f.scope.booth_id, f.flag_id))


def train_calibrator(train_dir, key_path) -> Calibrator:
    from .eval import load_key, matches  # key read only via explicit CLI path
    key = [p for p in load_key(key_path) if not p.is_benign]
    cal0 = Calibrator()
    raw = raw_flags(analyse(train_dir))
    flags = build_flags(raw, cal0)
    samples: dict = {}
    by_id = {f.flag_id: f for f in flags}
    for r in raw:
        fid = _fid(r["type"], r["scope"], r["metrics"])
        f = by_id[fid]
        y = int(any(matches(f, p) for p in key))
        xs, ys = samples.setdefault(r["type"], ([], []))
        xs.append(feature(r["type"], r.get("q"), r.get("score")))
        ys.append(y)
    return Calibrator().fit(samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--train-data")
    ap.add_argument("--train-key")
    a = ap.parse_args()
    t0 = time.time()
    cal = train_calibrator(a.train_data, a.train_key) if a.train_data and a.train_key else Calibrator()
    an = analyse(a.data)
    flags = build_flags(raw_flags(an), cal)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "flags.json").write_text(json.dumps([f.model_dump(mode="json") for f in flags], ensure_ascii=False, indent=1), encoding="utf-8")
    st = [s.model_dump(mode="json") for s in an["stories"].values()]
    for s in st:
        StoryResult.model_validate(s)
    (out / "stories.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    by = {}
    for f in flags:
        by[f.type] = by.get(f.type, 0) + 1
    print(f"flags={len(flags)} by_type={by} stories={len(st)} runtime_ms={int((time.time() - t0) * 1000)}")


if __name__ == "__main__":
    main()
