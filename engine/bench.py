"""python -m engine.run --bench [--scale 20] [--workers N]  ->  <out>/bench.json

Measured, not estimated (TRD 1.1): wall time per stage, duplicate pair counts (blocked vs naive n(n-1)/2),
the 500-resample bootstrap on the largest removed set, and with --scale N a clone of the district x N
(new voter, booth and ward IDs; booth-local structure kept, so it is a fair test of the engine) run serially
and per-ward in parallel.
"""
from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .data import Data, load


def clone(d: Data, k: int) -> Data:
    """District x k with new IDs. Copy 0 keeps the original IDs."""
    def roll(df):
        parts = []
        for i in range(k):
            c = df.copy()
            if i:
                c["voter_id"] = c.voter_id + f"-{i:02d}"
                c["booth_id"] = f"C{i:02d}" + c.booth_id
                c["ward_id"] = f"C{i:02d}" + c.ward_id
            parts.append(c)
        return pd.concat(parts, ignore_index=True)

    def ctx(df, cols):
        if df.empty:
            return df
        parts = []
        for i in range(k):
            c = df.copy()
            if i:
                for col in cols:
                    if col in c:
                        c[col] = f"C{i:02d}" + c[col].astype(str)
            parts.append(c)
        return pd.concat(parts, ignore_index=True)

    return Data(roll(d.v1), roll(d.v2), ctx(d.death, ["booth_id"]), ctx(d.hostel, ["booth_id"]),
                ctx(d.boundary, ["from_booth", "to_booth", "change_id"]))


def _bootstrap_ms(an: dict, n_boot: int = 500, reps: int = 5) -> dict:
    sizes = {}
    for s in an["stories"].values():
        sizes[s.booth_id] = s.removed_total
    booth = max(sizes, key=sizes.get)
    n = sizes[booth]
    arr = np.random.default_rng(0).integers(0, 5, n)
    rng = np.random.default_rng(42)
    best = 1e9
    for _ in range(reps):
        t = time.perf_counter()
        samp = arr[rng.integers(0, n, size=(n_boot, n))]
        boot = np.stack([(samp == j).mean(axis=1) for j in range(5)], axis=1)
        np.percentile(boot, [5, 95], axis=0)
        best = min(best, (time.perf_counter() - t) * 1000)
    return {"booth_id": booth, "removed_records": n, "resamples": n_boot, "ms_best_of_5": round(best, 2)}


def _one(label: str, d: Data, workers: int, data_dir=None) -> tuple[dict, dict]:
    from .run import analyse, build_flags, raw_flags
    from .confidence import Calibrator
    timings: dict = {}
    t = time.perf_counter()
    an = analyse(data_dir, timings=timings, workers=workers, data=d)
    t2 = time.perf_counter()
    flags = build_flags(raw_flags(an), Calibrator())
    timings["flags"] = round((time.perf_counter() - t2) * 1000, 1)
    total = round((time.perf_counter() - t) * 1000, 1)
    ps = an["pair_stats"]
    pairs = {v: {**ps[v], "reduction_x": round(ps[v]["naive_pairs"] / max(ps[v]["candidate_pairs"], 1), 1)} for v in ps}
    run = {"label": label, "n_v1": len(d.v1), "n_v2": len(d.v2), "booths": int(d.v1.booth_id.nunique()),
           "wards": int(d.v1.ward_id.nunique()), "workers": workers, "total_ms": total, "stages_ms": timings,
           "duplicate_pairs": pairs, "flags": len(flags), "duplicate_clusters_v2": len(an["clusters"]["v2"])}
    print(f"[bench] {label}: n_v1={run['n_v1']} workers={workers} total={total/1000:.1f}s "
          f"pairs_scored_v1={ps['v1']['candidate_pairs']} naive_v1={ps['v1']['naive_pairs']}")
    return run, an


def run_bench(a) -> dict:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cpus = os.cpu_count() or 1
    par = a.workers if a.workers > 1 else min(8, cpus)
    d = load(a.data)
    runs = []
    r1, an = _one("district", d, 1, data_dir=a.data)
    runs.append(r1)
    r2, _ = _one("district", d, par, data_dir=a.data)
    runs.append(r2)
    res = {"measured": True, "machine": {"cpus": cpus, "platform": platform.platform(), "python": platform.python_version()},
           "complexity": {"diff": "O(n) hash join", "booth_tests": "O(m log m), m booths",
                          "duplicates": "O(sum b_i^2) inside blocks, union-find merges", "stories": "O(r) lookups per booth",
                          "bootstrap": "O(B r), vectorised", "claim_tools": "O(1) lookups in aggregates.json"},
           "bootstrap": _bootstrap_ms(an), "runs": runs}
    if a.scale and a.scale > 1:
        big = clone(d, a.scale)
        s1, _ = _one(f"clone_x{a.scale}", big, 1)
        sN, _ = _one(f"clone_x{a.scale}", big, par)
        runs += [s1, sN]
        res["scale"] = {"factor": a.scale, "n_v1": s1["n_v1"], "serial_s": round(s1["total_ms"] / 1000, 1),
                        "parallel_s": round(sN["total_ms"] / 1000, 1), "workers": par,
                        "speedup_total": round(s1["total_ms"] / sN["total_ms"], 2),
                        "speedup_local_stages": round(
                            sum(s1["stages_ms"].get(k, 0) for k in ("duplicates_v1", "duplicates_v2", "rule_relation_conflict"))
                            / max(sN["stages_ms"].get("parallel_local_stages", 1), 1), 2),
                        "per_voter_us_serial": round(1000 * s1["total_ms"] / s1["n_v1"], 2),
                        "per_voter_us_district": round(1000 * r1["total_ms"] / r1["n_v1"], 2)}
    (out / "bench.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[bench] wrote {out / 'bench.json'}")
    return res
