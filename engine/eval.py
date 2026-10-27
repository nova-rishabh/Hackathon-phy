"""python -m engine.eval --data <dir> --flags flags.json --key answer_key.json --out eval.json

The ONLY module that reads an answer key (passed explicitly on the CLI; also used by run.py for the
training district's calibration).
A planting matches a flag when the flag type fits the planting type and (same booth OR voter_ids overlap).
hostel_moveout / boundary_change / mass_death plantings are deletion events, so they match deletion_spike.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts.models import EvalResult, Flag, Miss, Planting, ReliabilityBin, TypeScore

KIND_TO_FLAG = {"hostel_moveout": "deletion_spike", "boundary_change": "deletion_spike", "mass_death": "deletion_spike"}


def load_key(path) -> list[Planting]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Planting.model_validate(p) for p in raw]


def flag_type_of(p: Planting) -> str:
    return KIND_TO_FLAG.get(p.type, p.type)


def matches(f: Flag, p: Planting) -> bool:
    if f.type != flag_type_of(p):
        return False
    return f.scope.booth_id == p.booth_id or bool(set(f.scope.voter_ids) & set(p.voter_ids))


def evaluate(flags: list[Flag], key: list[Planting]) -> EvalResult:
    anomalies = [p for p in key if not p.is_benign]
    decoys = [p for p in key if p.is_benign]
    found, misses = 0, []
    tp = {}
    fn = {}
    for p in anomalies:
        t = flag_type_of(p)
        hit = [f for f in flags if matches(f, p) and not f.likely_benign]
        if hit:
            found += 1
            tp[t] = tp.get(t, 0) + 1
        else:
            fn[t] = fn.get(t, 0) + 1
            any_hit = [f for f in flags if matches(f, p)]
            misses.append(Miss(plant_id=p.plant_id, type=p.type,
                               why="flagged but judged likely benign" if any_hit else "no flag of this type at the planted location"))
    cleared = 0
    for p in decoys:
        if not any(matches(f, p) and not f.likely_benign for f in flags):
            cleared += 1
    fp = {}
    true_flags = []
    for f in flags:
        is_true = any(matches(f, p) for p in anomalies)
        true_flags.append(is_true)
        if not is_true:
            fp[f.type] = fp.get(f.type, 0) + 1
    types = sorted(set(tp) | set(fn) | set(fp))
    by_type = []
    for t in types:
        a, b, c = tp.get(t, 0), fp.get(t, 0), fn.get(t, 0)
        by_type.append(TypeScore(type=t, tp=a, fp=b, fn=c, precision=a / (a + b) if a + b else 0.0,
                                 recall=a / (a + c) if a + c else 0.0))
    edges = [0.0, 0.25, 0.5, 0.75, 1.0000001]
    rel = []
    for lo, hi in zip(edges, edges[1:]):
        idx = [i for i, f in enumerate(flags) if lo <= f.confidence < hi]
        if idx:
            rel.append(ReliabilityBin(bin_lo=lo, bin_hi=min(hi, 1.0), mean_conf=sum(flags[i].confidence for i in idx) / len(idx),
                                      frac_true=sum(true_flags[i] for i in idx) / len(idx), n=len(idx)))
    return EvalResult(planted_anomalies=len(anomalies), planted_decoys=len(decoys), found=found, decoys_cleared=cleared,
                      by_type=by_type, benign_fp_rate=(len(decoys) - cleared) / len(decoys) if decoys else 0.0,
                      reliability=rel, misses=misses)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")  # accepted for symmetry with engine.run; not needed
    ap.add_argument("--flags", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    flags = [Flag.model_validate(f) for f in json.loads(Path(a.flags).read_text(encoding="utf-8"))]
    res = evaluate(flags, load_key(a.key))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(res.model_dump_json(indent=1), encoding="utf-8")
    print(f"found {res.found}/{res.planted_anomalies}, decoys cleared {res.decoys_cleared}/{res.planted_decoys}")


if __name__ == "__main__":
    main()
