"""Precomputed aggregates for the Claim Court tools (TRD 1.1: O(1) lookups per sub-claim).

build_aggregates(analysis, flags) -> dict written by engine.run to artifacts/aggregates.json.
load_aggregates(path) + one helper per ClaimTool, each returning (value, query_shown, series):
    value        float | None (None = cannot be computed for that scope)
    query_shown  the plain-language query the UI shows as the "query chip"
    series       [{"label": str, "value": float}] -> contracts EvidencePoint list
Scopes: booth_id="B017", ward_id="W02", or neither (whole district). Rates and shares are percentages.
query(agg, tool, params) dispatches by ClaimTool name.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .stats import BANDS, band

BAND_LABELS = ["18-24", "25-34", "35-44", "45-59", "60-74", "75+"]
_ = BANDS  # labels follow stats.BANDS order


# ------------------------------------------------------------------ build

def _bands(ages: pd.Series) -> dict[str, int]:
    c = np.bincount(ages.map(band).to_numpy(dtype=int), minlength=len(BAND_LABELS)) if len(ages) else np.zeros(len(BAND_LABELS), int)
    return {lab: int(c[i]) for i, lab in enumerate(BAND_LABELS)}


def _gender(g: pd.Series) -> dict[str, int]:
    vc = g.value_counts()
    return {k: int(vc.get(k, 0)) for k in ("M", "F", "T")}


def _block(v1: pd.DataFrame, v2: pd.DataFrame, removed: pd.DataFrame, added: pd.DataFrame, n_dupe_clusters: int,
           n_dupe_records: int, story_counts: dict[str, int]) -> dict:
    n1, n2 = len(v1), len(v2)
    rem = len(removed)
    tot = sum(story_counts.values())
    return {
        "n_v1": n1, "n_v2": n2, "removed": rem, "added": len(added),
        "deletion_rate": round(100.0 * rem / n1, 3) if n1 else None,
        "addition_rate": round(100.0 * len(added) / n2, 3) if n2 else None,
        "duplicate_clusters": n_dupe_clusters, "duplicate_records": n_dupe_records,
        "age_bands": {"v1": _bands(v1.age), "v2": _bands(v2.age), "removed": _bands(removed.age), "added": _bands(added.age)},
        "gender": {"v1": _gender(v1.gender), "v2": _gender(v2.gender), "removed": _gender(removed.gender), "added": _gender(added.gender)},
        "story_counts": story_counts,
        "story_shares": {k: round(100.0 * v / tot, 2) if tot else 0.0 for k, v in story_counts.items()},
    }


def build_aggregates(a: dict, flags=None) -> dict:
    d, df = a["data"], a["diff"]
    v1, v2 = d.v1, d.v2
    removed, added = df["deleted"], df["added"]
    tests = a["tests"]
    dup = [f for f in (flags or []) if f.type == "duplicate_cluster"]
    if not dup:  # fall back to raw clusters (deduplicated across versions)
        seen = {tuple(c["voter_ids"]): c for ver in ("v2", "v1") for c in a["clusters"][ver]}
        dup_rows = [(c["booth_id"], len(k)) for k, c in seen.items()]
    else:
        dup_rows = [(f.scope.booth_id, len(f.scope.voter_ids)) for f in dup]
    dup_df = pd.DataFrame(dup_rows, columns=["booth_id", "n"])
    stories = {b: {s.code: s.count for s in r.stories} for b, r in a["stories"].items()}
    codes = sorted({c for s in stories.values() for c in s})
    ward_of = dict(zip(v1.booth_id, v1.ward_id)) | dict(zip(v2.booth_id, v2.ward_id))

    def scoped(col, val):
        f = (lambda x: x[x[col] == val]) if col else (lambda x: x)
        bs = [b for b, w in ward_of.items() if (col is None or (w if col == "ward_id" else b) == val)]
        dsub = dup_df[dup_df.booth_id.isin(bs)]
        sc = {c: int(sum(stories.get(b, {}).get(c, 0) for b in bs)) for c in codes}
        return _block(f(v1), f(v2), f(removed), f(added), len(dsub), int(dsub.n.sum()), sc)

    g1, g2 = dict(tuple(v1.groupby("booth_id"))), dict(tuple(v2.groupby("booth_id")))
    gr, ga = dict(tuple(removed.groupby("booth_id"))), dict(tuple(added.groupby("booth_id")))
    dcount = dup_df.groupby("booth_id").n.agg(["size", "sum"])
    empty1, empty2 = v1.iloc[:0], v2.iloc[:0]
    booths = {}
    for b in sorted(ward_of):
        sc = {c: int(stories.get(b, {}).get(c, 0)) for c in codes}
        blk = _block(g1.get(b, empty1), g2.get(b, empty2), gr.get(b, empty1), ga.get(b, empty2),
                     int(dcount["size"].get(b, 0)), int(dcount["sum"].get(b, 0)), sc)
        blk["ward_id"] = ward_of[b]
        if b in tests.index:
            t = tests.loc[b]
            blk["expected_removed"] = round(float(t.del_exp), 2)
            blk["deletion_q"] = float(t.del_q)
            blk["addition_q"] = float(t.add_q)
        booths[b] = blk
    order = sorted(booths, key=lambda b: (-booths[b]["removed"], b))
    for i, b in enumerate(order, 1):
        booths[b]["rank_by_removals"] = i
    wards = {w: scoped("ward_id", w) for w in sorted(set(ward_of.values()))}
    for w, blk in wards.items():
        blk["booths"] = sorted(b for b, x in ward_of.items() if x == w)
    worder = sorted(wards, key=lambda w: (-wards[w]["removed"], w))
    for i, w in enumerate(worder, 1):
        wards[w]["rank_by_removals"] = i
    return {"version": 1, "n_booths": len(booths), "n_wards": len(wards), "district": scoped(None, None),
            "booths": booths, "wards": wards, "band_labels": BAND_LABELS, "story_codes": codes}


# ------------------------------------------------------------------ load + query helpers

@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_aggregates(path: str | Path = "artifacts/aggregates.json") -> dict:
    p = Path(path)
    return _load(str(p), p.stat().st_mtime)


def _scope(agg: dict, booth_id=None, ward_id=None) -> tuple[dict | None, str]:
    if booth_id:
        return agg["booths"].get(str(booth_id)), f"booth {booth_id}"
    if ward_id:
        return agg["wards"].get(str(ward_id)), f"ward {ward_id}"
    return agg["district"], "the whole district"


def _pts(d: dict) -> list[dict]:
    return [{"label": str(k), "value": float(v)} for k, v in d.items()]


def _missing(where):
    return None, f"no data for {where}", []


def deletion_count(agg, booth_id=None, ward_id=None, **_):
    s, where = _scope(agg, booth_id, ward_id)
    if s is None:
        return _missing(where)
    series = [{"label": "removed", "value": float(s["removed"])}, {"label": "on roll v1", "value": float(s["n_v1"])}]
    if "expected_removed" in s:
        series.append({"label": "expected removed", "value": float(s["expected_removed"])})
    return float(s["removed"]), f"count of records in roll v1 and not in roll v2, {where}", series


def deletion_rate(agg, booth_id=None, ward_id=None, **_):
    s, where = _scope(agg, booth_id, ward_id)
    if s is None or s["deletion_rate"] is None:
        return _missing(where)
    series = [{"label": where, "value": float(s["deletion_rate"])},
              {"label": "district", "value": float(agg["district"]["deletion_rate"])}]
    return float(s["deletion_rate"]), f"removed / on roll v1 x 100, {where}", series


def addition_count(agg, booth_id=None, ward_id=None, **_):
    s, where = _scope(agg, booth_id, ward_id)
    if s is None:
        return _missing(where)
    return float(s["added"]), f"count of records in roll v2 and not in roll v1, {where}", [
        {"label": "added", "value": float(s["added"])}, {"label": "on roll v2", "value": float(s["n_v2"])}]


def duplicate_count(agg, booth_id=None, ward_id=None, **_):
    s, where = _scope(agg, booth_id, ward_id)
    if s is None:
        return _missing(where)
    return float(s["duplicate_records"]), f"records in cross-script duplicate clusters, {where}", [
        {"label": "clusters", "value": float(s["duplicate_clusters"])},
        {"label": "records", "value": float(s["duplicate_records"])}]


def age_distribution(agg, booth_id=None, ward_id=None, of="removed", band=None, **_):
    """Share (%) of `of` (removed | added | v1 | v2) in age band `band`; series = all bands."""
    s, where = _scope(agg, booth_id, ward_id)
    if s is None or of not in s["age_bands"]:
        return _missing(where)
    bands = s["age_bands"][of]
    tot = sum(bands.values())
    shares = {k: round(100.0 * v / tot, 2) if tot else 0.0 for k, v in bands.items()}
    val = shares.get(str(band)) if band else None
    q = f"age-band shares of {of} records, {where}" + (f", band {band}" if band else "")
    return val, q, _pts(shares)


def gender_ratio(agg, booth_id=None, ward_id=None, of="v2", **_):
    """Females per 1000 males for `of` (v1 | v2 | removed | added); series = v1 and v2."""
    s, where = _scope(agg, booth_id, ward_id)
    if s is None or of not in s["gender"]:
        return _missing(where)

    def r(g):
        return round(1000.0 * g["F"] / g["M"], 1) if g["M"] else None
    val = r(s["gender"][of])
    series = [{"label": k, "value": float(r(s["gender"][k]))} for k in ("v1", "v2") if r(s["gender"][k]) is not None]
    return val, f"females per 1000 males among {of} records, {where}", series


METRICS = {"removed", "added", "deletion_rate", "addition_rate", "duplicate_records", "n_v1", "n_v2"}


def compare_booths(agg, booth_a=None, booth_b=None, metric="deletion_rate", **_):
    """value = metric(booth_a) - metric(booth_b)."""
    a, b = agg["booths"].get(str(booth_a)), agg["booths"].get(str(booth_b))
    if a is None or b is None or metric not in METRICS or a.get(metric) is None or b.get(metric) is None:
        return None, f"compare {metric} of booth {booth_a} and booth {booth_b}: not available", []
    return float(a[metric] - b[metric]), f"{metric} of booth {booth_a} minus booth {booth_b}", [
        {"label": str(booth_a), "value": float(a[metric])}, {"label": str(booth_b), "value": float(b[metric])}]


def story_shares(agg, booth_id=None, ward_id=None, code="unexplained", **_):
    """Share (%) of removed records attributed to story `code`; series = every story."""
    s, where = _scope(agg, booth_id, ward_id)
    if s is None:
        return _missing(where)
    return s["story_shares"].get(str(code)), f"share of removed records attributed to '{code}', {where}", _pts(s["story_shares"])


def booth_rank(agg, booth_id=None, **_):
    s = agg["booths"].get(str(booth_id))
    if s is None:
        return _missing(f"booth {booth_id}")
    return float(s["rank_by_removals"]), f"rank of booth {booth_id} by removed records (1 = most) of {agg['n_booths']}", [
        {"label": "rank", "value": float(s["rank_by_removals"])}, {"label": "booths", "value": float(agg["n_booths"])}]


TOOLS = {"deletion_count": deletion_count, "deletion_rate": deletion_rate, "addition_count": addition_count,
         "duplicate_count": duplicate_count, "age_distribution": age_distribution, "gender_ratio": gender_ratio,
         "compare_booths": compare_booths, "story_shares": story_shares}


def query(agg: dict, tool: str, params: dict | None = None):
    """Dispatch a ClaimTool. 'unanswerable' (or an unknown tool) -> (None, reason, [])."""
    fn = TOOLS.get(tool)
    if fn is None:
        return None, "this question cannot be answered from roll data", []
    return fn(agg, **(params or {}))
