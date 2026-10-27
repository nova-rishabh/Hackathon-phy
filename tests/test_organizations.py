"""Tests for Organization Workspaces, RBAC Roles, Quotas, and API Keys."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from api.organizations import enforce_quota


def test_organizations_lifecycle_and_rbac():
    client = TestClient(app)

    # 1. Default org is present
    r = client.get("/orgs")
    assert r.status_code == 200
    orgs = r.json()
    assert len(orgs) >= 1
    default_org = orgs[0]
    org_id = default_org["id"]

    # 2. Create a new organization workspace
    create_res = client.post(
        "/orgs",
        json={
            "name": "Association for Democratic Audits",
            "slug": "ada-audit",
            "tier": "enterprise",
            "admin_email": "lead@ada-audit.org",
        },
    )
    assert create_res.status_code == 200
    ada_org = create_res.json()
    ada_id = ada_org["id"]
    assert ada_org["tier"] == "enterprise"
    assert ada_org["quotas"]["checks_limit"] == 50000

    from api import wa_auth
    admin_token = wa_auth.make_token("+919876543210")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Add members with different roles
    add_auditor = client.post(
        f"/orgs/{ada_id}/members",
        headers=admin_headers,
        json={"email": "auditor_sam@ada-audit.org", "role": "auditor"},
    )
    assert add_auditor.status_code == 200
    assert add_auditor.json()["role"] == "auditor"

    add_reviewer = client.post(
        f"/orgs/{ada_id}/members",
        headers=admin_headers,
        json={"email": "reviewer_priya@ada-audit.org", "role": "reviewer"},
    )
    assert add_reviewer.status_code == 200
    assert add_reviewer.json()["role"] == "reviewer"

    # List members
    members_res = client.get(f"/orgs/{ada_id}/members", headers=admin_headers)
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 3  # owner + auditor + reviewer

    # 4. Generate an API Key for the auditor
    key_res = client.post(
        f"/orgs/{ada_id}/keys",
        headers=admin_headers,
        json={
            "name": "Automated CI/CD Constituency Scanner",
            "role": "auditor",
            "scopes": ["audit:read", "audit:write", "search"],
            "expires_in_days": 30,
        },
    )
    assert key_res.status_code == 200
    key_data = key_res.json()
    raw_token = key_data["token"]
    key_id = key_data["key_id"]
    assert raw_token.startswith("rw_live_")

    # List keys - plaintext token must NOT be present
    keys_list_res = client.get(f"/orgs/{ada_id}/keys", headers=admin_headers)
    assert keys_list_res.status_code == 200
    keys_list = keys_list_res.json()
    assert len(keys_list) >= 1
    found_key = next((k for k in keys_list if k["key_id"] == key_id), None)
    assert found_key is not None
    assert "token" not in found_key
    assert found_key["last4"] == raw_token[-4:]

    # 5. Authenticate with X-API-Key against /auth/whoami
    whoami_res = client.get("/auth/whoami", headers={"X-API-Key": raw_token})
    assert whoami_res.status_code == 200
    whoami = whoami_res.json()
    assert whoami["auth_type"] == "api_key"
    assert whoami["role"] == "auditor"
    assert whoami["organization"]["id"] == ada_id
    assert "audit:write" in whoami["scopes"]

    # 6. Usage and quota consumption
    usage_res = client.get(f"/orgs/{ada_id}/usage", headers=admin_headers)
    assert usage_res.status_code == 200
    usage = usage_res.json()
    assert usage["checks_limit"] == 50000
    assert usage["pdf_ingest_allowed"] is True

    # Test atomic quota enforcement
    enforce_quota(ada_id, count=10)
    usage_res2 = client.get(f"/orgs/{ada_id}/usage", headers=admin_headers)
    assert usage_res2.json()["checks_used"] == 10

    # 7. Revoke API key and verify subsequent calls are denied with 401
    rev_res = client.delete(f"/orgs/{ada_id}/keys/{key_id}", headers=admin_headers)
    assert rev_res.status_code == 200

    denied_res = client.get("/auth/whoami", headers={"X-API-Key": raw_token})
    assert denied_res.status_code == 401


if __name__ == "__main__":
    test_organizations_lifecycle_and_rbac()
    print("Organization, RBAC, quota, and API key tests passed successfully!")
