"""Load roll_v1/roll_v2 + context tables from a data directory.

Supported layouts: <dir>/roll_v1.{parquet,csv} + context csvs at top level (fixtures), or
<dir>/artifacts/roll_v*.parquet + <dir>/artifacts/context/*.csv (generator output),
or <dir>/roll_v*.* + <dir>/context/*.csv.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

CONTEXT_FILES = {"death": "death_register.csv", "hostel": "hostel_list.csv", "boundary": "boundary_changes.csv"}
STR_COLS = ["voter_id", "roll_version", "ward_id", "booth_id", "house_no", "name_dev", "name_lat",
            "relation_type", "relation_name_dev", "relation_name_lat", "gender"]


@dataclass
class Data:
    v1: pd.DataFrame
    v2: pd.DataFrame
    death: pd.DataFrame
    hostel: pd.DataFrame
    boundary: pd.DataFrame


def member(a, b) -> np.ndarray:
    """Boolean mask: which values of `a` are in `b`. A hash lookup on object arrays: O(len(a) + len(b)).
    (pandas' Arrow-string isin is ~20x slower at 1M rows.)"""
    s = b if isinstance(b, (set, frozenset)) else set(b)
    return np.fromiter((x in s for x in a), dtype=bool, count=len(a))


def _find(dirs: list[Path], stem: str) -> Path | None:
    for d in dirs:
        for ext in (".parquet", ".csv"):
            p = d / (stem + ext)
            if p.exists():
                return p
    return None


def _roll(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, dtype=str, encoding="utf-8", keep_default_na=False)
    for c in STR_COLS:
        df[c] = df[c].astype(str)
    df["age"] = df["age"].astype(int)
    df["serial_no"] = df["serial_no"].astype(int)
    return df.reset_index(drop=True)


def _ctx(dirs: list[Path], fname: str, cols: list[str]) -> pd.DataFrame:
    for d in dirs:
        p = d / fname
        if p.exists():
            return pd.read_csv(p, dtype=str, encoding="utf-8", keep_default_na=False)
    return pd.DataFrame(columns=cols)


def load(data_dir: str | Path) -> Data:
    d = Path(data_dir)
    roll_dirs = [d, d / "artifacts"]
    ctx_dirs = [d, d / "context", d / "artifacts" / "context"]
    p1, p2 = _find(roll_dirs, "roll_v1"), _find(roll_dirs, "roll_v2")
    if not p1 or not p2:
        raise FileNotFoundError(f"roll_v1/roll_v2 not found under {d}")
    return Data(
        _roll(p1), _roll(p2),
        _ctx(ctx_dirs, CONTEXT_FILES["death"], ["booth_id", "house_no", "name_lat", "age", "date"]),
        _ctx(ctx_dirs, CONTEXT_FILES["hostel"], ["booth_id", "house_no", "capacity", "academic_year_end"]),
        _ctx(ctx_dirs, CONTEXT_FILES["boundary"], ["change_id", "from_booth", "to_booth", "house_from", "house_to", "effective_date"]),
    )
