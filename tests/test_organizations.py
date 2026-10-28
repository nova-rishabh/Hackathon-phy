"""Organization workspaces, roles, quotas and API keys, under the secure model: roles come from membership in a
specific workspace; the signed-in creator becomes owner; nobody grants above their own role."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from api import wa_auth
from api.organizations import enforce_quota

OP = {"X-WA-Secret": os.environ.get("WA_WORKER_SECRET", "")}
owner = {"Authorization": "Bearer " + wa_auth.make_token("+919876543210")}
stranger = {"Authorization": "Bearer " + wa_auth.make_token("+919812345678")}


def test_organizations_lifecycle_and_rbac():
    client = TestClient(app)

    # A signed-in user creates a workspace and becomes its owner. Paid tiers come through billing, so a
    # self-service workspace starts free; the operator can set a tier directly.
    ada = client.post("/orgs", headers=owner, json={"name": "Democratic Audits Desk", "tier": "enterprise"})
    assert ada.status_code == 200, ada.text
    ada = ada.json()
    ada_id = ada["id"]
    assert ada["tier"] == "free"
    paid = client.post("/orgs", headers=OP, json={"name": "Paid Desk", "tier": "enterprise", "admin_email": "+919876543210"})
    assert paid.status_code == 200 and paid.json()["tier"] == "enterprise"
    paid_id = paid.json()["id"]

    # The owner sees their workspaces; a stranger sees none of them.
    mine = {o["id"] for o in client.get("/orgs", headers=owner).json()}
    assert {ada_id, paid_id} <= mine
    assert not ({ada_id, paid_id} & {o["id"] for o in client.get("/orgs", headers=stranger).json()})

    # Members with different roles (seat limit on the free tier is 2: owner + one).
    r = client.post(f"/orgs/{paid_id}/members", headers=owner, json={"email": "auditor_sam@desk.org", "role": "auditor"})
    assert r.status_code == 200 and r.json()["role"] == "auditor"
    r = client.post(f"/orgs/{paid_id}/members", headers=owner, json={"email": "reviewer_priya@desk.org", "role": "reviewer"})
    assert r.status_code == 200
    members = client.get(f"/orgs/{paid_id}/members", headers=owner).json()
    assert len(members) == 3

    # API key for the auditor; the secret is shown once and never listed.
    key = client.post(f"/orgs/{paid_id}/keys", headers=owner,
                      json={"name": "Constituency scanner", "role": "auditor", "expires_in_days": 30}).json()
    raw, key_id = key["token"], key["key_id"]
    assert raw.startswith("rw_live_")
    listed = client.get(f"/orgs/{paid_id}/keys", headers=owner).json()
    found = next(k for k in listed if k["key_id"] == key_id)
    assert "token" not in found and found["last4"] == raw[-4:]

    who = client.get("/auth/whoami", headers={"X-API-Key": raw}).json()
    assert who["auth_type"] == "api_key" and who["role"] == "auditor" and who["organization"]["id"] == paid_id

    # Usage and atomic quota.
    usage = client.get(f"/orgs/{paid_id}/usage", headers=owner).json()
    assert usage["checks_limit"] == 50000 and usage["pdf_ingest_allowed"] is True
    enforce_quota(paid_id, count=10)
    assert client.get(f"/orgs/{paid_id}/usage", headers=owner).json()["checks_used"] == 10

    # Revoked keys stop working.
    assert client.delete(f"/orgs/{paid_id}/keys/{key_id}", headers=owner).status_code == 200
    assert client.get("/auth/whoami", headers={"X-API-Key": raw}).status_code == 401


if __name__ == "__main__":
    test_organizations_lifecycle_and_rbac()
    print("Organization, RBAC, quota, and API key tests passed successfully!")
