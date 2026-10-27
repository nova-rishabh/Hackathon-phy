"""Tests for blind-district evaluation and confidence curve recalibration from reviewer outcomes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from api.reports import _audit_path
from contracts.models import AuditEntry, Flag
from engine.confidence import Calibrator, band_of, feature


def test_calibrator_recalibrate_from_reviews():
    cal = Calibrator()
    # Baseline synthetic samples: deletion_spike
    base_samples = {
        "deletion_spike": (
            [1.0, 2.0, 3.0, 1.5, 2.5, 0.5, 3.5],
            [0, 0, 1, 0, 1, 0, 1],
        )
    }

    # Flags mapping
    flags_by_id = {
        "flag_del_1": {
            "type": "deletion_spike",
            "metrics": {"q_value": 0.001, "observed": 45},
        },
        "flag_del_2": {
            "type": "deletion_spike",
            "metrics": {"q_value": 0.04, "observed": 15},
        },
    }

    # Reviewer entries in immutable ledger format
    entries = [
        AuditEntry(
            ts="2026-10-28T05:00:00Z",
            flag_id="flag_del_1",
            action="review:escalated",
            note_h="hash1",
            who="senior_auditor@rollwatch.internal",
            prev_hash="GENESIS",
            hash="h1",
        ),
        AuditEntry(
            ts="2026-10-28T05:01:00Z",
            flag_id="flag_del_2",
            action="review:benign",
            note_h="hash2",
            who="senior_auditor@rollwatch.internal",
            prev_hash="h1",
            hash="h2",
        ),
    ]

    res = cal.recalibrate_from_reviews(
        flags_by_id=flags_by_id,
        audit_entries=entries,
        base_samples=base_samples,
        reviewer_weight=4.0,
    )

    assert res["status"] == "recalibrated"
    assert res["reviewed_cases_incorporated"] == 2
    assert "deletion_spike" in res["recalibrated_models"]
    assert cal.recalibrated_reviews_count == 2
    assert cal.last_recalibrated_at is not None

    # Predict with recalibrated curve
    conf_high, n = cal.predict("deletion_spike", 3.0)
    conf_low, _ = cal.predict("deletion_spike", 0.5)
    assert conf_high > conf_low
    assert n == 9  # 7 base + 2 reviews

    state = cal.to_dict()
    assert "deletion_spike" in state["models"]
    assert "coef" in state["models"]["deletion_spike"]
    assert "intercept" in state["models"]["deletion_spike"]


def test_api_recalibrate_endpoint():
    client = TestClient(app)

    # 1. Check review queue
    q_resp = client.get("/review/queue?limit=5")
    assert q_resp.status_code == 200
    queue = q_resp.json()
    items = queue.get("items", [])
    assert len(items) > 0
    flag_id = items[0]["flag_id"]

    # 2. Submit a human review verdict with signed reviewer token
    from api import wa_auth
    token = wa_auth.make_token("+919876543210")
    rev_resp = client.post(
        f"/review/{flag_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "escalated",
            "note": "Verified field investigation confirms sudden unexplained roll subtraction.",
        },
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["review"]["status"] == "escalated"
    assert rev_data["audit_hash"] is not None

    # 3. Trigger recalibration
    recal_resp = client.post("/audit/recalibrate?reviewer_weight=3.5")
    assert recal_resp.status_code == 200
    recal_data = recal_resp.json()
    assert recal_data["status"] in ("recalibrated", "skipped")
    assert "calibrator_state" in recal_data or "reviewed_cases_incorporated" in recal_data


def test_blind_district_evaluation_artifacts():
    # Verify generated blind districts exist and have valid evaluation metrics
    alpha_dir = Path("artifacts_blind/district_alpha")
    assert (alpha_dir / "roll_v1.parquet").exists()
    assert (alpha_dir / "roll_v2.parquet").exists()
    assert (alpha_dir / "flags.json").exists()
    assert (alpha_dir / "eval.json").exists()

    eval_json = json.loads((alpha_dir / "eval.json").read_text(encoding="utf-8"))
    assert eval_json["found"] >= 7
    assert eval_json["decoys_cleared"] >= 3
    print(f"Blind district alpha: found={eval_json['found']}, decoys_cleared={eval_json['decoys_cleared']}")


if __name__ == "__main__":
    test_calibrator_recalibrate_from_reviews()
    test_api_recalibrate_endpoint()
    test_blind_district_evaluation_artifacts()
    print("All recalibration and blind district tests passed!")
