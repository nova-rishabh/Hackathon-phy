"""Access-control checks: every attack below must be refused. Each line is one hole found in review."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from api import wa_auth

OP = {"X-WA-Secret": os.environ.get("WA_WORKER_SECRET", "")}
alice = {"Authorization": "Bearer " + wa_auth.make_token("+919000000001")}
mallory = {"Authorization": "Bearer " + wa_auth.make_token("+919000000002")}


def check(label: str, got: int, ok: set[int]):
    assert got in ok, f"{label}: got {got}, expected one of {sorted(ok)}"
    print(f"  refused as expected  {label:58s} {got}")


def test_access_control():
    c = TestClient(app)
    org = c.post("/orgs", headers=alice, json={"name": "Alice Desk"}).json()["id"]
    key = c.post(f"/orgs/{org}/keys", headers=alice, json={"name": "viewer key", "role": "viewer"}).json()["token"]
    other = c.post("/orgs", headers=mallory, json={"name": "Mallory Desk"}).json()["id"]

    # organisations
    check("anonymous lists workspaces", c.get("/orgs").status_code, {401})
    check("anonymous creates a workspace", c.post("/orgs", json={"name": "x"}).status_code, {401})
    check("stranger reads another workspace", c.get(f"/orgs/{org}", headers=mallory).status_code, {404})
    check("stranger adds himself to another workspace",
          c.post(f"/orgs/{org}/members", headers=mallory, json={"email": "+919000000002", "role": "owner"}).status_code, {404})
    check("stranger mints a key for another workspace",
          c.post(f"/orgs/{org}/keys", headers=mallory, json={"name": "k", "role": "owner"}).status_code, {404})
    check("key from one workspace acts on another",
          c.get(f"/orgs/{other}/members", headers={"X-API-Key": key}).status_code, {404})
    check("viewer key adds a member", c.post(f"/orgs/{org}/members", headers={"X-API-Key": key},
                                             json={"email": "z", "role": "viewer"}).status_code, {403})
    admin_key = c.post(f"/orgs/{org}/keys", headers=alice, json={"name": "admin key", "role": "admin"}).json()["token"]
    check("admin grants owner (above own role)", c.post(f"/orgs/{org}/members", headers={"X-API-Key": admin_key},
                                                        json={"email": "y", "role": "owner"}).status_code, {403})
    check("self-service workspace on a paid tier",
          0 if c.post("/orgs", headers=alice, json={"name": "free?", "tier": "enterprise"}).json()["tier"] == "free" else 1, {0})
    check("forged operator secret", c.get("/orgs", headers={"X-WA-Secret": "nope"}).status_code, {403})

    # billing
    for path in ("/billing/subscriptions", "/billing/events", "/billing/subscriptions/sub_x", "/billing/subscriptions/sub_x/quotas"):
        check(f"anonymous reads {path}", c.get(path).status_code, {403, 503})
    check("anonymous cancels a subscription", c.post("/billing/subscriptions/sub_x/cancel").status_code, {403, 503})

    # reports and reviews
    check("anonymous recalibrates live confidence", c.post("/audit/recalibrate").status_code, {403, 503})
    check("anonymous batch review", c.post("/review/batch", json={"flag_ids": [], "status": "benign"}).status_code, {401})

    # jobs
    j = c.post("/jobs/audit", json={"roll_v1_csv": "a", "roll_v2_csv": "b"})
    if j.status_code == 200:
        jid = j.json()["job_id"]
        check("anonymous reads someone's job", c.get(f"/jobs/{jid}").status_code, {404})
        check("anonymous reads someone's result", c.get(f"/jobs/{jid}/result").status_code, {404})
        check("anonymous cancels someone's job", c.post(f"/jobs/{jid}/cancel").status_code, {404})
        check("wrong job token", c.get(f"/jobs/{jid}", headers={"X-Job-Token": "guess"}).status_code, {404})
        assert c.get(f"/jobs/{jid}", headers={"X-Job-Token": j.json()["job_token"]}).status_code == 200
    check("anonymous lists all jobs", c.get("/jobs").status_code, {403, 503})

    # monitoring
    check("anonymous fakes a heartbeat", c.post("/ops/monitoring/heartbeat", json={"component": "whatsapp", "state": "ok"}).status_code, {403, 503})
    check("anonymous injects an error", c.post("/ops/monitoring/error", json={"component": "api", "message": "x"}).status_code, {403, 503})
    check("anonymous reads error details", c.get("/ops/monitoring/errors").status_code, {403, 503})
    check("anonymous triggers outbound probe", c.get("/ops/monitoring/probe").status_code, {403, 503})

    # the legitimate operator still gets through
    assert c.get("/billing/subscriptions", headers=OP).status_code == 200
    assert c.get("/jobs", headers=OP).status_code == 200
    assert c.post("/ops/monitoring/heartbeat", headers=OP, json={"component": "telegram", "state": "ok"}).status_code == 200


if __name__ == "__main__":
    test_access_control()
    print("ALL ACCESS-CONTROL CHECKS PASSED")
