"""Roll v1 -> v2 diff (TRD 4)."""
from __future__ import annotations

import pandas as pd

COMPARE = ["ward_id", "booth_id", "house_no", "name_dev", "name_lat", "relation_type",
           "relation_name_dev", "relation_name_lat", "age", "gender"]


def diff(v1: pd.DataFrame, v2: pd.DataFrame) -> dict:
    """added (v2 only), deleted (v1 only), modified (in both, any field differs; a booth change counts)."""
    ids1, ids2 = set(v1.voter_id), set(v2.voter_id)
    added = v2[~v2.voter_id.isin(ids1)]
    deleted = v1[~v1.voter_id.isin(ids2)]
    both = v1[v1.voter_id.isin(ids2)].set_index("voter_id")[COMPARE].join(
        v2.set_index("voter_id")[COMPARE], rsuffix="_2", how="inner")
    changed = pd.Series(False, index=both.index)
    fields: dict[str, list[str]] = {}
    for c in COMPARE:
        m = both[c].astype(str) != both[c + "_2"].astype(str)
        changed |= m
        for vid in both.index[m]:
            fields.setdefault(vid, []).append(c)
    modified = v2[v2.voter_id.isin(both.index[changed])]
    return {"added": added, "deleted": deleted, "modified": modified, "changed_fields": fields}
