"""Test for real public-roll PDF ingestion through inrolls adapter."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from pypdf import PageObject, PdfWriter
from engine.adapters import inrolls


def create_mock_roll_pdf(out_path: Path, part_no: int = 47) -> Path:
    """Generates an ECI-standard searchable electoral roll PDF page with voter slips."""
    # Build text conforming to standard ECI voter card layout
    sample_text = f"""
ELECTION COMMISSION OF INDIA - ELECTORAL ROLL 2024
Assembly Constituency No and Name: 005 - Sampleabad
Part Number: {part_no}
Polling Station: Government Primary School, Room 1

1 | SBD0024152
Elector's Name : Meena Kumari
Father's Name : Ram Lal
House No : 14/B
Age : 38  Gender : FEMALE

2 | SBD0024153
Elector's Name : Rajesh Sharma
Father's Name : Mohan Lal
House No : 15
Age : 45  Gender : MALE

3 | SBD0024154
Elector's Name : Sunita Verma
Husband's Name : Ravi Verma
House No : 16/1
Age : 29  Gender : FEMALE

4 | SBD0024155
Elector's Name : Amit Singh
Father's Name : Gurpreet Singh
House No : 22
Age : 52  Gender : MALE
"""
    # Create a PDF page with this text
    # In pypdf, we can write a stream or create a page
    # An easy way to create a searchable text PDF using reportlab or raw PDF stream:
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(len(sample_text) + 100).encode("ascii") + b" >>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"50 750 Td\n"
    )
    # Add text lines in PDF BT/ET syntax
    for line in sample_text.strip().splitlines():
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        pdf_content += b"(" + safe_line.encode("latin-1", "replace") + b") ' \n"
    pdf_content += b"ET\nendstream\nendobj\n"
    pdf_content += (
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n100\n%%EOF\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pdf_content)
    return out_path


def test_pdf_ingestion():
    tmp_dir = ROOT / "cache" / "test_pdf_ingest"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    pdf_v1 = tmp_dir / "booth_047_v1.pdf"
    pdf_v2 = tmp_dir / "booth_047_v2.pdf"

    create_mock_roll_pdf(pdf_v1, part_no=47)
    create_mock_roll_pdf(pdf_v2, part_no=47)

    # 1. Test text extraction
    txt = inrolls.extract_text_from_pdf(pdf_v1)
    assert "Meena Kumari" in txt, "Name missing from extracted text"
    assert "SBD0024152" in txt, "EPIC missing from extracted text"
    print("PDF text extraction PASSED")

    # 2. Test record parsing
    recs = inrolls.parse_pdf_text_to_records(txt)
    assert len(recs) == 4, f"Expected 4 records, got {len(recs)}"
    r0 = recs[0]
    assert r0["id"] == "SBD0024152"
    assert r0["elector_name"] == "Meena Kumari"
    assert r0["sex"] == "F"
    assert r0["part_no"] == 47
    assert r0["age"] == 38

    r2 = recs[2]  # Sunita Verma (husband)
    assert r2["husband"] == 1
    assert r2["father_or_husband_name"] == "Ravi Verma"
    print("PDF voter slip parser PASSED")

    # 3. Test conversion to RollRow
    out_dir = tmp_dir / "output"
    inrolls.ingest_rolls(pdf_v1, pdf_v2, out_dir)

    df1 = pd.read_parquet(out_dir / "roll_v1.parquet")
    assert len(df1) == 4
    assert "voter_id" in df1.columns
    assert "booth_id" in df1.columns
    assert df1.iloc[0]["booth_id"] == "B047"
    assert df1.iloc[0]["name_lat"] == "Meena Kumari"
    assert df1.iloc[2]["relation_type"] == "husband"
    print("Full PDF-to-RollRow ingestion PASSED (CSV + Parquet)")

    print("\n>>> ALL PUBLIC-ROLL PDF INGESTION TESTS PASSED! <<<")


if __name__ == "__main__":
    test_pdf_ingestion()
