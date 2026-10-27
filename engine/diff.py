"""Roll v1 -> v2 diff (TRD 4). Hash join on voter_id, vectorised field compare: O(n)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import member

COMPARE = ["ward_id", "booth_id", "house_no", "name_dev", "name_lat", "relation_type",
           "relation_name_dev", "relation_name_lat", "age", "gender"]


def diff(v1: pd.DataFrame, v2: pd.DataFrame) -> dict:
    """added (v2 only), deleted (v1 only), modified (in both, any field differs; a booth change counts).
    Age is compared after the roll-wide age shift (the modal v2-v1 age difference, normally +1 for a roll one
    year later), so ordinary ageing is not a modification."""
    in2 = member(v1.voter_id, v2.voter_id)
    in1 = member(v2.voter_id, v1.voter_id)
    added, deleted = v2[~in1], v1[~in2]
    both = v1.loc[in2, ["voter_id"] + COMPARE].merge(v2.loc[in1, ["voter_id"] + COMPARE], on="voter_id", suffixes=("", "_2"))
    dage = both["age_2"].to_numpy(dtype=int) - both["age"].to_numpy(dtype=int)
    shift = int(pd.Series(dage).mode().iloc[0]) if len(dage) else 0
    cols = {c: both[c].to_numpy(dtype=object) != both[c + "_2"].to_numpy(dtype=object) for c in COMPARE if c != "age"}
    cols["age"] = dage != shift
    names = list(cols)
    m = np.column_stack([cols[c] for c in names]) if names else np.zeros((len(both), 0), bool)
    changed = m.any(axis=1)
    vids = both.voter_id.to_numpy(dtype=object)[changed]
    fields = {vid: [c for c, x in zip(names, row) if x] for vid, row in zip(vids, m[changed])}
    modified = v2[member(v2.voter_id, vids)]
    return {"added": added, "deleted": deleted, "modified": modified, "changed_fields": fields, "age_shift": shift}
