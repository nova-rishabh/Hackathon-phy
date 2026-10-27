"""Test for asynchronous constituency-level audit jobs."""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ROLLWATCH_DATA", str(ROOT / "artifacts"))

from fastapi.testclient import TestClient
from api.main import app

def test_async_jobs_flow():
    client = TestClient(app)
    sample_dir = ROOT / "web" / "public" / "sample"
    v1_csv = (sample_dir / "roll_v1.csv").read_text(encoding="utf-8")
    v2_csv = (sample_dir / "roll_v2.csv").read_text(encoding="utf-8")
    death_csv = (sample_dir / "death_register.csv").read_text(encoding="utf-8") if (sample_dir / "death_register.csv").exists() else None

    # 1. Submit async audit job
    payload = {
        "constituency_id": "AC005-Sampleabad",
        "roll_v1_csv": v1_csv,
        "roll_v2_csv": v2_csv,
        "death_register_csv": death_csv,
    }
    resp = client.post("/jobs/audit", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    job_id = data["job_id"]
    print("Submitted async job:", job_id, "status:", data["status"])

    # 2. Poll job status until completed (timeout 20s)
    t0 = time.time()
    completed = False
    while time.time() - t0 < 25:
        st_resp = client.get(f"/jobs/{job_id}")
        assert st_resp.status_code == 200
        st = st_resp.json()
        print(f"Polling job {job_id}: {st['status']} ({st['progress']['percent']}%) - {st['progress']['stage']}")
        if st["status"] == "completed":
            completed = True
            break
        elif st["status"] == "failed":
            raise RuntimeError(f"Job failed: {st.get('error')}")
        time.sleep(0.5)

    assert completed, f"Job did not complete within timeout. Current status: {st['status']}"

    # 3. Fetch full result
    res_resp = client.get(f"/jobs/{job_id}/result")
    assert res_resp.status_code == 200, res_resp.text
    result = res_resp.json()
    assert result["flags_total"] > 0
    assert len(result["stories"]) > 0
    print(f"Audit completed: {result['flags_total']} flags, {len(result['stories'])} booths in {result['runtime_ms']} ms")

    # 4. List jobs
    list_resp = client.get("/jobs?limit=5")
    assert list_resp.status_code == 200
    jobs = list_resp.json()["jobs"]
    assert any(j["job_id"] == job_id for j in jobs)
    print("Job listed in /jobs endpoint")

    print("\n>>> ALL ASYNC AUDIT JOBS CHECKS PASSED! <<<")


if __name__ == "__main__":
    test_async_jobs_flow()
