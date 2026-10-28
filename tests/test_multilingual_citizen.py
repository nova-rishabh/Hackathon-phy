"""Tests for multilingual citizen assistant across supported Indian languages."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from api import constants as C


def test_multilingual_citizen_ask():
    client = TestClient(app)

    # Test all 7 supported Indian languages
    languages_to_test = ["en", "hi", "pa", "bn", "mr", "ta", "te"]

    for lang in languages_to_test:
        resp = client.post(
            "/citizen/ask",
            json={
                "text": "meena kumari booth 47",
                "lang": lang,
                "channel": "web",
            },
        )
        assert resp.status_code == 200, f"Failed for language {lang}: {resp.text}"
        data = resp.json()
        assert data["lang"] == lang
        assert data["status"] in ("present", "modified", "not_in_new_list", "not_found")
        assert len(data["next_steps"]) > 0
        assert len(data["answer_text"]) > 0
        assert "1950" in data["answer_text"]  # Official helpline in procedural footer


def test_portal_and_scam_lines_defined():
    for lang in ("en", "hi", "pa", "bn", "mr", "ta", "te"):
        assert lang in C.PORTAL_LINE
        assert lang in C.SCAM_LINE
        assert "1950" in C.PORTAL_LINE[lang]
        assert "BLO" in C.SCAM_LINE[lang] or "बीएलओ" in C.SCAM_LINE[lang] or "ਬੀਐਲਓ" in C.SCAM_LINE[lang]


if __name__ == "__main__":
    test_portal_and_scam_lines_defined()
    test_multilingual_citizen_ask()
    print("All multilingual citizen tests passed!")
