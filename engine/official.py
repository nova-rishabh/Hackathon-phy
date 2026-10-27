"""Official "logical discrepancy" checks, as publicly reported for the 2025-26 SIR (thresholds vary by state and
were never fully published; these follow the West Bengal / Karnataka reporting). We run them on the roll and
publish how often each fires on records that hide no anomaly. They are never raised as flags.

Not checkable from a roll, so not run: siblings born under 9 months apart (rolls carry ages in whole years),
an "invalid" linked parent and weak documents (both need the enumeration forms).
"""
from __future__ import annotations

import pandas as pd

from .dupes import norm

PARENT_GAP_MIN, PARENT_GAP_MAX, GRANDPARENT_GAP_MIN, MANY_CHILDREN = 15, 50, 40, 6

CHECKS = {
    "official_parent_age_gap": f"parent under {PARENT_GAP_MIN} or over {PARENT_GAP_MAX} years older than the elector",
    "official_grandparent_age_gap": f"grandparent under {GRANDPARENT_GAP_MIN} years older than the elector",
    "official_many_children": f"{MANY_CHILDREN} or more electors listed as children of one parent",
    "official_name_changed": "the elector's own name differs from the previous roll",
    "official_relative_name_changed": "the father's or husband's name differs from the previous roll",
    "official_relation_type_changed": "the relation type differs from the previous roll (e.g. father vs husband)",
    "official_age_progression": "the age did not move by the gap between the two rolls",
}


def _links(v2: pd.DataFrame) -> pd.DataFrame:
    """Elector -> the parent's own record in the same house (unique normalised-name match), as the mapping does."""
    d = v2[["voter_id", "booth_id", "house_no", "name_lat", "relation_type", "relation_name_lat", "age"]].copy()
    d["k"], d["rk"] = d.name_lat.map(norm), d.relation_name_lat.map(norm)
    cnt = d.groupby(["booth_id", "house_no", "k"]).voter_id.transform("size")
    rel = d[cnt == 1][["booth_id", "house_no", "k", "voter_id", "age"]].rename(
        columns={"k": "rk", "voter_id": "p_id", "age": "p_age"})
    m = d[d.relation_type.isin(["father", "mother"])].merge(rel, on=["booth_id", "house_no", "rk"])
    return m[m.p_id != m.voter_id][["voter_id", "booth_id", "age", "p_id", "p_age"]]


def _items(df: pd.DataFrame, cols=("voter_id",)) -> list[dict]:
    return [{"booth_id": r.booth_id, "voter_ids": sorted({getattr(r, c) for c in cols})} for r in df.itertuples()]


def run(v1: pd.DataFrame, v2: pd.DataFrame) -> dict:
    out = {}
    ln = _links(v2)
    gap = ln.p_age - ln.age
    out["official_parent_age_gap"] = _items(ln[(gap < PARENT_GAP_MIN) | (gap > PARENT_GAP_MAX)], ("voter_id", "p_id"))
    gp = ln.merge(ln[["voter_id", "p_id", "p_age"]].rename(columns={"voter_id": "p_id", "p_id": "g_id", "p_age": "g_age"}), on="p_id")
    out["official_grandparent_age_gap"] = _items(gp[gp.g_age - gp.age < GRANDPARENT_GAP_MIN], ("voter_id", "g_id"))
    kids = ln.groupby(["booth_id", "p_id"]).voter_id.apply(list)
    out["official_many_children"] = [{"booth_id": b, "voter_ids": sorted(ids + [p])} for (b, p), ids in kids.items()
                                     if len(ids) >= MANY_CHILDREN]
    both = v1.merge(v2, on="voter_id", suffixes=("_1", "_2"))
    both = both.assign(booth_id=both.booth_id_2)
    s = lambda c: both[c].fillna("").astype(str).str.strip()
    out["official_name_changed"] = _items(both[(s("name_lat_1") != s("name_lat_2")) | (s("name_dev_1") != s("name_dev_2"))])
    out["official_relative_name_changed"] = _items(both[(s("relation_name_lat_1") != s("relation_name_lat_2"))
                                                        | (s("relation_name_dev_1") != s("relation_name_dev_2"))])
    out["official_relation_type_changed"] = _items(both[s("relation_type_1") != s("relation_type_2")])
    step = both.age_2 - both.age_1
    shift = int(step.median()) if len(step) else 0  # the gap between the two rolls, in years
    out["official_age_progression"] = _items(both[step != shift])
    return {k: {"definition": CHECKS[k], "items": v} for k, v in out.items()}
