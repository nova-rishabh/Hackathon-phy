"""Rule checks (TRD 4.4). Each returns a list of dicts consumed by engine.run."""
from __future__ import annotations

import pandas as pd
from rapidfuzz.distance import JaroWinkler

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
    """Fires only when the named relative's own record is found in the same house AND the pair is inconsistent
    (relative has the wrong gender for the relation, or is not older than a child)."""
    out = []
    for (booth, house), grp in v2.groupby(["booth_id", "house_no"]):
        if len(grp) < 2:
            continue
        rows = list(grp.itertuples())
        normed = {r.voter_id: norm(r.name_lat) for r in rows}
        for r in rows:
            if r.relation_type == "other":
                continue
            rel = norm(r.relation_name_lat)
            for o in rows:
                if o.voter_id == r.voter_id or JaroWinkler.similarity(rel, normed[o.voter_id]) < 0.92:
                    continue
                why = None
                if r.relation_type == "father" and (o.gender != "M" or o.age < r.age + 12):
                    why = "father_not_male_or_not_older"
                elif r.relation_type == "mother" and (o.gender != "F" or o.age < r.age + 12):
                    why = "mother_not_female_or_not_older"
                elif r.relation_type == "husband" and (o.gender != "M" or r.gender != "F"):
                    why = "husband_gender_mismatch"
                if why:
                    out.append({"booth_id": booth, "house_no": house, "voter_ids": [r.voter_id, o.voter_id], "why": why})
                break
    return out
