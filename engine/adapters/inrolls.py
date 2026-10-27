"""Adapter: parsed Indian electoral-roll CSVs -> the open RollWatch roll schema (contracts.models.RollRow columns).

Input is the CSV that the open-source in-rolls parser for searchable English roll PDFs writes
(github.com/in-rolls/electoral_rolls_parse_searchable; columns `number, id, elector_name, father_or_husband_name,
husband, house_no, age, sex, ac_name, part_no, ...`). Only the column names are relied on; no code is copied.
Two versions of the same constituency (draft and final, or two revisions) become roll_v1.csv and roll_v2.csv,
and the engine runs unchanged:

    python -m engine.adapters.inrolls --v1 old.csv --v2 new.csv --out data/ac_005
    python -m engine.run --data data/ac_005 --out data/ac_005

Real rolls are personal data: run this only where you may lawfully hold them, keep outputs booth-level, and never
publish names. RollWatch itself ships only the synthetic district.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OUT_COLS = ["voter_id", "roll_version", "ward_id", "booth_id", "serial_no", "house_no", "name_dev", "name_lat",
            "relation_type", "relation_name_dev", "relation_name_lat", "age", "gender"]


def _gender(s) -> str:
    s = str(s).strip().upper()
    return "F" if s.startswith("F") else "M" if s.startswith("M") else "T"


def convert(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """One parsed roll -> RollRow columns. Part number is the booth (polling station); ten parts make a ward."""
    part = pd.to_numeric(df["part_no"], errors="coerce").fillna(0).astype(int)
    husband = pd.to_numeric(df.get("husband", 0), errors="coerce").fillna(0).astype(int) == 1
    out = pd.DataFrame({
        "voter_id": df["id"].astype(str).str.strip(),
        "roll_version": version,
        "ward_id": "W" + (part // 10 + 1).astype(str).str.zfill(2),
        "booth_id": "B" + part.astype(str).str.zfill(3),
        "serial_no": pd.to_numeric(df["number"], errors="coerce").fillna(0).astype(int),
        "house_no": df["house_no"].fillna("").astype(str).str.strip(),
        "name_dev": "",  # English rolls; a native-script roll would fill this
        "name_lat": df["elector_name"].fillna("").astype(str).str.strip(),
        "relation_type": husband.map({True: "husband", False: "father"}),
        "relation_name_dev": "",
        "relation_name_lat": df["father_or_husband_name"].fillna("").astype(str).str.strip(),
        "age": pd.to_numeric(df["age"], errors="coerce").fillna(-1).astype(int),
        "gender": df["sex"].map(_gender),
    })
    return out[(out.voter_id != "") & (out.voter_id.str.lower() != "nan")][OUT_COLS]


def main():
    ap = argparse.ArgumentParser(prog="python -m engine.adapters.inrolls")
    ap.add_argument("--v1", required=True, help="parsed CSV of the earlier roll")
    ap.add_argument("--v2", required=True, help="parsed CSV of the later roll")
    ap.add_argument("--out", required=True, help="folder for roll_v1.csv and roll_v2.csv")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for v, src in (("v1", a.v1), ("v2", a.v2)):
        df = convert(pd.read_csv(src, dtype=str), v)
        df.to_csv(out / f"roll_{v}.csv", index=False, encoding="utf-8")
        print(f"roll_{v}: {len(df)} electors in {df.booth_id.nunique()} booths")


if __name__ == "__main__":
    main()
