"""Tests for Reports, Reviewer Workflow, and Data Quality/Provenance."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ROLLWATCH_DATA", str(ROOT / "artifacts"))

from fastapi.testclient import TestClient
from api.main import app

def test_reports_and_review_workflow():
    client = TestClient(app)

    # 1. Tamper-evident hash chain verification
    v_resp = client.get("/review/verify")
    assert v_resp.status_code == 200, v_resp.text
    v_data = v_resp.json()
    assert v_data["valid"] is True
    print("Hash chain verification PASSED (valid=True, length:", v_data["chain_length"], ")")

    # 2. Priority review queue
    q_resp = client.get("/review/queue?limit=5")
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "items" in q_data
    assert q_data["total"] > 0
    sample_flag_id = q_data["items"][0]["flag_id"]
    print("Review queue PASSED (total open flags:", q_data["total"], ")")

    # 3. Batch review
    b_resp = client.post("/review/batch", json={"flag_ids": [sample_flag_id], "status": "escalated", "note": "Verified by newsroom desk"})
    assert b_resp.status_code == 200
    assert b_resp.json()["updated_count"] == 1
    print("Batch review submission PASSED")

    # 4. Review history for flag
    h_resp = client.get(f"/review/history/{sample_flag_id}")
    assert h_resp.status_code == 200
    assert len(h_resp.json()["history"]) >= 1
    print("Flag review history timeline PASSED")

    # Verify chain integrity after new entry
    v_after = client.get("/review/verify").json()
    assert v_after["valid"] is True
    print("Hash chain remains valid after new block added (head:", v_after["head_hash"][:12], ")")

    # 5. Data quality report
    dq_resp = client.get("/reports/quality")
    assert dq_resp.status_code == 200
    dq = dq_resp.json()
    assert "total_electors" in dq
    assert "demographics" in dq
    assert "quality_score_pct" in dq
    print(f"Data quality report PASSED (score: {dq['quality_score_pct']}%, median age: {dq['demographics']['median_age']})")

    # 6. Provenance report
    pv_resp = client.get("/reports/provenance")
    assert pv_resp.status_code == 200
    pv = pv_resp.json()
    assert "dataset_checksums" in pv
    assert "roll_v1.parquet" in pv["dataset_checksums"]
    print("Cryptographic provenance certificate PASSED")

    # 7. Newsroom report (Markdown and HTML)
    nr_md = client.get("/reports/newsroom?format=markdown")
    assert nr_md.status_code == 200
    assert "# ROLLWATCH AUDIT REPORT" in nr_md.text
    print("Newsroom Markdown briefing PASSED")

    nr_html = client.get("/reports/newsroom?format=html")
    assert nr_html.status_code == 200
    assert "<h1>" in nr_html.text or "RollWatch Audit Report" in nr_html.text
    print("Newsroom HTML briefing PASSED")

    # 8. CSV Exports
    csv_flags = client.get("/reports/export/flags.csv")
    assert csv_flags.status_code == 200
    assert "flag_id,booth_id" in csv_flags.text
    print("Flags CSV export PASSED")

    csv_booths = client.get("/reports/export/booths.csv")
    assert csv_booths.status_code == 200
    assert "booth_id,outcome" in csv_booths.text
    print("Booths CSV export PASSED")

    print("\n>>> ALL REPORTS, REVIEW WORKFLOW, AND PROVENANCE TESTS PASSED! <<<")


if __name__ == "__main__":
    test_reports_and_review_workflow()
