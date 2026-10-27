"""Rule checks (TRD 4.4). Each returns a list of dicts consumed by engine.run."""
from __future__ import annotations

import pandas as pd

from .dupes import norm


def impossible_age(v2: pd.DataFrame) -> list[dict]:
    bad = v2[(v2.age < 18) | (v2.age > 110)]
    return [{"booth_id": r.booth_id, "house_no": r.house_no, "voter_ids": [r.voter_id], "age": int(r.age)}
            for r in bad.itertuples()]


def oversized_household(v2: pd.DataFrame, limit: int = 15) -> list[dict]:
    g = v2.groupby(["booth_id", "house_no"]).voter_id.apply(list)
    return [{"booth_id": b, "house_no": h, "voter_ids": ids, "size": len(ids)}
            for (b, h), ids in g.items() if len(ids) > limit]


def gender_ratio_swing(v1: pd.DataFrame, v2: pd.DataFrame, pts: float = 8.0, min_n: int = 30) -> list[dict]:
    """Female share of (M+F) per booth; flag when it moves by more than `pts` points.
    min_n skips booths too small for a share to mean anything."""
    def share(df):
        d = df[df.gender.isin(["M", "F"])]
        g = d.groupby("booth_id").gender.agg(n="size", f=lambda s: int((s == "F").sum()))
        g["share"] = 100.0 * g.f / g.n
        return g
    a, b = share(v1), share(v2)
    out = []
    for booth in a.index.intersection(b.index):
        if min(a.n[booth], b.n[booth]) < min_n:
            continue
        sw = float(b.share[booth] - a.share[booth])
        if abs(sw) > pts:
            out.append({"booth_id": booth, "swing": sw, "n": int(b.n[booth])})
    return out


def relation_conflict(v2: pd.DataFrame) -> list[dict]:
    """Fires only when the named relative's own record is found in the same house (exact normalised-name match,
    exactly one candidate) AND the pair is impossible: a father/mother who is not older than the elector, or a
    'husband' whose record is not male (or an elector listed with a husband who is not female).
    A female relative under 'father' is NOT fired: the old form field read "father's/husband's name" and that
    mislabel is a known innocent explanation. One flag per household, listing every conflicting pair."""
    d = v2[["voter_id", "booth_id", "house_no", "name_lat", "relation_type", "relation_name_lat", "age", "gender"]].copy()
    d["k"] = d.name_lat.map(norm)
    d["rk"] = d.relation_name_lat.map(norm)
    cnt = d.groupby(["booth_id", "house_no", "k"]).voter_id.transform("size")
    rel = d[cnt == 1][["booth_id", "house_no", "k", "voter_id", "age", "gender"]].rename(
        columns={"k": "rk", "voter_id": "o_id", "age": "o_age", "gender": "o_gender"})
    m = d[d.relation_type != "other"].merge(rel, on=["booth_id", "house_no", "rk"], how="inner")
    m = m[m.o_id != m.voter_id]
    parent = m.relation_type.isin(["father", "mother"]) & (m.o_age <= m.age)
    husb = (m.relation_type == "husband") & ((m.o_gender != "M") | (m.gender != "F"))
    m = m.assign(why=None)
    m.loc[parent, "why"] = "parent_not_older"
    m.loc[husb, "why"] = "husband_gender_mismatch"
    m = m[m.why.notna()]
    out = []
    for (booth, house), g in m.groupby(["booth_id", "house_no"], sort=True):
        ids = sorted(set(g.voter_id) | set(g.o_id))
        out.append({"booth_id": booth, "house_no": house, "voter_ids": ids, "pairs": len(g),
                    "whys": sorted(set(g.why))})
    return out
