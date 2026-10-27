"""Adapter: parsed Indian electoral-roll CSVs & public roll PDFs -> open RollWatch schema.

Supports:
1. Parsed CSVs from the open in-rolls parser (github.com/in-rolls/electoral_rolls_parse_searchable)
2. Real public-roll searchable PDFs published by ECI / State CEOs (per booth/part)
3. Direct directory ingestion of booth PDFs into roll_v1 and roll_v2 (CSV + Parquet)

Usage:
    # From PDFs:
    python -m engine.adapters.inrolls --v1 rolls_v1/ --v2 rolls_v2/ --out data/ac_005
    # From single PDFs:
    python -m engine.adapters.inrolls --v1 booth_47_v1.pdf --v2 booth_47_v2.pdf --out data/b047
    # From parsed CSVs:
    python -m engine.adapters.inrolls --v1 old.csv --v2 new.csv --out data/ac_005
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path
from typing import Any

import pandas as pd

OUT_COLS = [
    "voter_id", "roll_version", "ward_id", "booth_id", "serial_no", "house_no",
    "name_dev", "name_lat", "relation_type", "relation_name_dev", "relation_name_lat",
    "age", "gender"
]

# Standard ECI EPIC Regex: 3 uppercase letters followed by 7 digits, or state code alphanumeric format
EPIC_RE = re.compile(r"([A-Z]{3}[0-9]{7}|[A-Z]{2}/[0-9]+/[0-9]+/[0-9]+|SBD[0-9]{7})(?![0-9])")
PART_NO_RE = re.compile(r"(?:Part\s*(?:No\.?|Number)|Polling\s*Station\s*(?:No\.?|Number))\s*[:\-]?\s*(\d+)", re.I)
SERIAL_RE = re.compile(r"^\s*(\d{1,4})\s*$")


def _gender(s) -> str:
    s = str(s).strip().upper()
    return "F" if s.startswith("F") else "M" if s.startswith("M") else "T"


def convert(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """One parsed roll DataFrame -> RollRow columns. Part number is booth; 10 parts make a ward."""
    part_series = df["part_no"] if "part_no" in df.columns else 1
    part = pd.to_numeric(part_series, errors="coerce").fillna(1).astype(int)
    husband_series = df["husband"] if "husband" in df.columns else 0
    husband = pd.to_numeric(husband_series, errors="coerce").fillna(0).astype(int) == 1

    def _col_str(name: str) -> pd.Series:
        if name in df.columns:
            return df[name].fillna("").astype(str).str.strip()
        return pd.Series("", index=df.index, dtype=str)

    number_series = pd.to_numeric(df["number"], errors="coerce").fillna(0).astype(int) if "number" in df.columns else 0
    age_series = pd.to_numeric(df["age"], errors="coerce").fillna(-1).astype(int) if "age" in df.columns else -1
    sex_series = df["sex"].map(_gender) if "sex" in df.columns else pd.Series("M", index=df.index)

    out = pd.DataFrame({
        "voter_id": df["id"].astype(str).str.strip(),
        "roll_version": version,
        "ward_id": "W" + (part // 10 + 1).astype(str).str.zfill(2),
        "booth_id": "B" + part.astype(str).str.zfill(3),
        "serial_no": number_series,
        "house_no": _col_str("house_no"),
        "name_dev": _col_str("name_dev"),
        "name_lat": _col_str("elector_name"),
        "relation_type": husband.map({True: "husband", False: "father"}),
        "relation_name_dev": _col_str("relation_name_dev"),
        "relation_name_lat": _col_str("father_or_husband_name"),
        "age": age_series,
        "gender": sex_series,
    })
    return out[(out.voter_id != "") & (out.voter_id.str.lower() != "nan")][OUT_COLS]


# ------------------------------------------------------------------ PDF Ingestion
def extract_text_from_pdf(pdf_source: str | Path | bytes) -> str:
    """Extract raw text from PDF bytes or path using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf is required for PDF roll ingestion. Run: uv pip install pypdf")

    stream = io.BytesIO(pdf_source) if isinstance(pdf_source, bytes) else pdf_source
    reader = PdfReader(stream)
    pages = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        pages.append(txt)
    return "\n--- PAGE ---\n".join(pages)


def parse_pdf_text_to_records(text: str, default_part: int = 1) -> list[dict[str, Any]]:
    """Parses raw text extracted from an ECI-standard voter roll PDF into structured voter records.

    Uses robust EPIC-anchored slip segmentation that handles arbitrary line wraps,
    concatenated streams, OCR artifacts, and multi-column card layouts.
    """
    part_match = PART_NO_RE.search(text[:3000])
    part_no = int(part_match.group(1)) if part_match else default_part

    epic_matches = list(EPIC_RE.finditer(text))
    if not epic_matches:
        return []

    records: list[dict[str, Any]] = []
    for i, m in enumerate(epic_matches):
        epic_id = m.group(1)
        start_idx = m.start()
        end_idx = epic_matches[i + 1].start() if i + 1 < len(epic_matches) else len(text)

        pre_text = text[max(0, start_idx - 35):start_idx]
        card_text = text[start_idx:end_idx]

        # Serial number in prefix or card
        serial = i + 1
        ser_m = re.search(r"(\d{1,4})\s*[|:\-]?\s*$", pre_text.strip())
        if ser_m:
            serial = int(ser_m.group(1))

        # Elector Name
        name = ""
        nm_m = re.search(
            r"(?:Elector(?:.s)?\s*Name|Name)\s*[:\-]\s*([A-Za-z\s.]+?)(?=(?:Father|Husband|Mother|Other|House|Age|Gender|Sex|\d+\s*[|:\-]|$))",
            card_text, re.I
        )
        if nm_m:
            name = nm_m.group(1).strip()

        # Relative Name & Type
        rel_name = ""
        is_husband = 0
        rel_m = re.search(
            r"(Father|Husband|Mother|Other)(?:.s)?\s*Name\s*[:\-]\s*([A-Za-z\s.]+?)(?=(?:House|Age|Gender|Sex|\d+\s*[|:\-]|$))",
            card_text, re.I
        )
        if rel_m:
            is_husband = 1 if rel_m.group(1).lower() == "husband" else 0
            rel_name = rel_m.group(2).strip()

        # House Number
        house_no = ""
        hn_m = re.search(
            r"(?:House\s*(?:No\.?|Number)|H\.No)\s*[:\-]\s*([A-Za-z0-9\-/,\s]+?)(?=(?:Age|Gender|Sex|\d+\s*[|:\-]|$))",
            card_text, re.I
        )
        if hn_m:
            house_no = hn_m.group(1).strip()

        # Age
        age = -1
        ag_m = re.search(r"Age\s*[:\-]\s*(\d{1,3})", card_text, re.I)
        if ag_m:
            age = int(ag_m.group(1))

        # Gender
        gender = "M"
        sx_m = re.search(r"(?:Gender|Sex)\s*[:\-]\s*(MALE|FEMALE|THIRD\s*GENDER|M|F|T)", card_text, re.I)
        if sx_m:
            gender = _gender(sx_m.group(1))

        records.append({
            "number": serial,
            "id": epic_id,
            "elector_name": name,
            "father_or_husband_name": rel_name,
            "husband": is_husband,
            "house_no": house_no,
            "age": age,
            "sex": gender,
            "part_no": part_no,
        })

    return records


def ingest_path(src_path: Path, version: str) -> pd.DataFrame:
    """Ingest a CSV file, a single PDF, or a directory of PDFs."""
    if src_path.is_dir():
        # Directory of PDFs or CSVs
        dfs = []
        for p in sorted(src_path.iterdir()):
            if p.suffix.lower() == ".pdf":
                txt = extract_text_from_pdf(p)
                recs = parse_pdf_text_to_records(txt)
                if recs:
                    dfs.append(pd.DataFrame(recs))
            elif p.suffix.lower() == ".csv":
                dfs.append(pd.read_csv(p, dtype=str))
        if not dfs:
            raise ValueError(f"No PDF or CSV roll files found in {src_path}")
        combined = pd.concat(dfs, ignore_index=True)
        return convert(combined, version)

    if src_path.suffix.lower() == ".pdf":
        txt = extract_text_from_pdf(src_path)
        recs = parse_pdf_text_to_records(txt)
        if not recs:
            raise ValueError(f"No voter records could be extracted from {src_path}")
        return convert(pd.DataFrame(recs), version)

    # Default: CSV format
    return convert(pd.read_csv(src_path, dtype=str), version)


def ingest_rolls(v1: Path, v2: Path, out_dir: Path):
    """Parses v1 and v2 sources and writes roll_v1/v2 CSV and Parquet files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for ver, src in (("v1", v1), ("v2", v2)):
        df = ingest_path(src, ver)
        csv_path = out_dir / f"roll_{ver}.csv"
        parquet_path = out_dir / f"roll_{ver}.parquet"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_parquet(parquet_path, index=False)
        print(f"roll_{ver}: {len(df)} electors across {df.booth_id.nunique()} booths ({parquet_path.name})")


def main():
    ap = argparse.ArgumentParser(prog="python -m engine.adapters.inrolls", description="RollWatch Voter Roll Ingestion Adapter")
    ap.add_argument("--v1", required=True, help="earlier roll: path to CSV, PDF, or directory of PDFs")
    ap.add_argument("--v2", required=True, help="later roll: path to CSV, PDF, or directory of PDFs")
    ap.add_argument("--out", required=True, help="destination directory for roll_v1 and roll_v2")
    args = ap.parse_args()

    ingest_rolls(Path(args.v1), Path(args.v2), Path(args.out))


if __name__ == "__main__":
    main()
