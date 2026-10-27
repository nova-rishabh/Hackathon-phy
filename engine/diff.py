"""Roll v1 -> v2 diff (TRD 4). Hash join on voter_id, vectorised field compare: O(n)."""
from __future__ import annotations

import pandas as pd

COMPARE = ["ward_id", "booth_id", "house_no", "name_dev", "name_lat", "relation_type",
           "relation_name_dev", "relation_name_lat", "age", "gender"]


def diff(v1: pd.DataFrame, v2: pd.DataFrame) -> dict:
    """added (v2 only), deleted (v1 only), modified (in both, any field differs; a booth change counts)."""
    in2 = v1.voter_id.isin(v2.voter_id)
    in1 = v2.voter_id.isin(v1.voter_id)
    added, deleted = v2[~in1], v1[~in2]
    both = v1.loc[in2, ["voter_id"] + COMPARE].merge(v2.loc[in1, ["voter_id"] + COMPARE], on="voter_id", suffixes=("", "_2"))
    mask = pd.DataFrame({c: both[c].astype(str).values != both[c + "_2"].astype(str).values for c in COMPARE},
                        index=both.voter_id.values)
    changed = mask.any(axis=1)
    fields: dict[str, list[str]] = {}
    sub = mask[changed]
    for vid, row in zip(sub.index, sub.values):
        fields[vid] = [c for c, m in zip(COMPARE, row) if m]
    modified = v2[v2.voter_id.isin(set(changed.index[changed.values]))]
    return {"added": added, "deleted": deleted, "modified": modified, "changed_fields": fields}
