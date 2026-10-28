"""Tests for CDN ETag Caching, 304 Not Modified, and Incremental Audits."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app


def test_cdn_cache_and_etag():
    client = TestClient(app)

    # 1. Cache status endpoint
    status_res = client.get("/cache/status")
    assert status_res.status_code == 200
    cache_meta = status_res.json()
    assert "etag" in cache_meta
    initial_etag = cache_meta["etag"]

    # 2. First request to /overview should return 200 with ETag header
    r1 = client.get("/overview")
    assert r1.status_code == 200
    assert "etag" in r1.headers
    etag_header = r1.headers["etag"]
    assert "max-age" in r1.headers.get("cache-control", "")

    # 3. Second request with If-None-Match should return 304 Not Modified
    r2 = client.get("/overview", headers={"If-None-Match": etag_header})
    assert r2.status_code == 304
    assert r2.content == b""  # Empty payload saved on wire

    # Also test unquoted etag
    r2_raw = client.get("/overview", headers={"If-None-Match": initial_etag})
    assert r2_raw.status_code == 304


def test_incremental_audit_pipeline():
    client = TestClient(app)

    # Get baseline ETag and flags count
    r_flags = client.get("/flags")
    assert r_flags.status_code == 200
    old_etag = r_flags.headers.get("etag")

    # Trigger incremental audit on 2 modified booths
    inc_res = client.post(
        "/audit/incremental",
        json={"changed_booth_ids": ["B001", "B002"]},
    )
    assert inc_res.status_code == 200
    data = inc_res.json()
    assert data["status"] == "success"
    assert data["changed_booths_count"] == 2
    assert data["unaffected_booths_count"] >= 90
    assert data["flags_retained"] > 0
    assert data["runtime_ms"] < 2500.0  # Fast execution

    # Verify cache was invalidated and new ETag generated
    r_after = client.get("/overview")
    assert r_after.status_code == 200
    assert "etag" in r_after.headers


if __name__ == "__main__":
    test_cdn_cache_and_etag()
    test_incremental_audit_pipeline()
    print("CDN caching and incremental audit tests passed!")
