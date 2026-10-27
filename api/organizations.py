"""Organization workspaces, role-based access control (RBAC), quotas, and API key management."""
from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Security
from fastapi.security import APIKeyHeader

from api.store import data_dir
from api import wa_auth
from contracts.models import (
    AddMemberRequest,
    ApiKeyItem,
    CreateKeyRequest,
    CreateKeyResponse,
    CreateOrgRequest,
    Organization,
    OrgMember,
    OrgRole,
    OrgTier,
    QuotaInfo,
)

router = APIRouter(prefix="", tags=["organizations", "auth"])
_LOCK = threading.RLock()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

ROLE_HIERARCHY: dict[OrgRole, int] = {
    "owner": 100,
    "admin": 80,
    "auditor": 60,
    "reviewer": 40,
    "viewer": 20,
}

TIER_QUOTAS: dict[OrgTier, QuotaInfo] = {
    "free": QuotaInfo(checks_limit=100, checks_used=0, max_seats=2, seats_used=1, rate_limit_per_min=30, pdf_ingest=False),
    "pro": QuotaInfo(checks_limit=2500, checks_used=0, max_seats=10, seats_used=1, rate_limit_per_min=120, pdf_ingest=True),
    "enterprise": QuotaInfo(checks_limit=50000, checks_used=0, max_seats=100, seats_used=1, rate_limit_per_min=600, pdf_ingest=True),
}


def _store_file() -> Path:
    return data_dir() / "organizations.json"


def _load_data() -> dict[str, Any]:
    p = _store_file()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Initialize default demo organization
    now = datetime.now(timezone.utc).isoformat()
    default_org_id = "org_demo_watch"
    default_data = {
        "organizations": {
            default_org_id: {
                "id": default_org_id,
                "name": "Civil Society Roll Watch",
                "slug": "cs-watch",
                "tier": "pro",
                "quotas": TIER_QUOTAS["pro"].model_dump(),
                "created_at": now,
            }
        },
        "members": {
            default_org_id: [
                {
                    "member_id": "mem_default_admin",
                    "email": "lead_auditor@rollwatch.internal",
                    "role": "owner",
                    "joined_at": now,
                }
            ]
        },
        "api_keys": {},
    }
    _save_data(default_data)
    return default_data


def _save_data(data: dict[str, Any]):
    p = _store_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _hash_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- Authentication & RBAC Helper
class AuthenticatedContext:
    def __init__(
        self,
        auth_type: str,
        user_or_key: str,
        org: Organization,
        role: OrgRole,
        scopes: list[str],
    ):
        self.auth_type = auth_type
        self.user_or_key = user_or_key
        self.org = org
        self.role = role
        self.scopes = scopes


def get_current_auth(
    x_api_key: str | None = Security(API_KEY_HEADER),
    authorization: str | None = Header(None),
) -> AuthenticatedContext:
    """Resolves caller context from X-API-Key header or Bearer JWT token."""
    with _LOCK:
        data = _load_data()

        # 1. Try X-API-Key
        if x_api_key:
            hashed = _hash_key(x_api_key)
            matched_key = None
            for key_id, kdata in data["api_keys"].items():
                if kdata.get("hashed_secret") == hashed and kdata.get("is_active", True):
                    matched_key = kdata
                    # Update last used
                    kdata["last_used_at"] = datetime.now(timezone.utc).isoformat()
                    _save_data(data)
                    break

            if matched_key:
                org_data = data["organizations"].get(matched_key["org_id"])
                if not org_data:
                    raise HTTPException(401, "organization associated with API key not found")
                org = Organization.model_validate(org_data)
                return AuthenticatedContext(
                    auth_type="api_key",
                    user_or_key=matched_key["key_id"],
                    org=org,
                    role=matched_key["role"],
                    scopes=matched_key.get("scopes", []),
                )
            raise HTTPException(401, "invalid or revoked API key")

        # 2. Try Bearer token
        tok = (authorization or "").removeprefix("Bearer ").strip()
        user_id = wa_auth.read_token(tok) if tok else None
        if user_id:
            # Default to first organization for authenticated user
            default_org_data = list(data["organizations"].values())[0]
            org = Organization.model_validate(default_org_data)
            return AuthenticatedContext(
                auth_type="bearer",
                user_or_key=user_id,
                org=org,
                role="admin",
                scopes=["*"],
            )

        # 3. Allow anonymous dev fallback for development/demo ease
        default_org_data = list(data["organizations"].values())[0]
        org = Organization.model_validate(default_org_data)
        return AuthenticatedContext(
            auth_type="anonymous",
            user_or_key="anonymous_dev",
            org=org,
            role="viewer",
            scopes=["audit:read", "search"],
        )


def enforce_quota(org_id: str, count: int = 1) -> QuotaInfo:
    """Atomic quota check and increment. Raises 429 if limit is exceeded."""
    with _LOCK:
        data = _load_data()
        org_data = data["organizations"].get(org_id)
        if not org_data:
            raise HTTPException(404, f"organization {org_id} not found")
        quotas = org_data["quotas"]
        if quotas["checks_used"] + count > quotas["checks_limit"]:
            raise HTTPException(
                429,
                f"organization quota exceeded ({quotas['checks_used']}/{quotas['checks_limit']} checks used). Please upgrade workspace tier.",
            )
        quotas["checks_used"] += count
        _save_data(data)
        return QuotaInfo.model_validate(quotas)


def enforce_role(current_role: OrgRole, required_role: OrgRole):
    """Enforces role hierarchy."""
    if ROLE_HIERARCHY.get(current_role, 0) < ROLE_HIERARCHY.get(required_role, 0):
        raise HTTPException(
            403,
            f"Insufficient permissions: requires {required_role} role or higher (current: {current_role})",
        )


# ---------------------------------------------------------------- Workspace Endpoints
@router.post("/orgs", response_model=Organization)
def create_organization(
    req: CreateOrgRequest,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Create a new organization workspace with designated tier and quota limits."""
    slug = req.slug or req.name.lower().replace(" ", "-").replace("_", "-")
    org_id = f"org_{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc).isoformat()
    tier_quotas = TIER_QUOTAS.get(req.tier, TIER_QUOTAS["pro"])

    new_org = Organization(
        id=org_id,
        name=req.name,
        slug=slug,
        tier=req.tier,
        quotas=tier_quotas.model_copy(),
        created_at=now,
    )

    with _LOCK:
        data = _load_data()
        data["organizations"][org_id] = new_org.model_dump()
        data["members"][org_id] = [
            {
                "member_id": f"mem_{secrets.token_hex(4)}",
                "email": req.admin_email,
                "role": "owner",
                "joined_at": now,
            }
        ]
        _save_data(data)

    return new_org


@router.get("/orgs", response_model=list[Organization])
def list_organizations(auth: AuthenticatedContext = Depends(get_current_auth)):
    """List all available workspaces."""
    with _LOCK:
        data = _load_data()
        return [Organization.model_validate(v) for v in data["organizations"].values()]


@router.get("/orgs/{org_id}", response_model=Organization)
def get_organization(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    """Retrieve workspace details and real-time quota status."""
    with _LOCK:
        data = _load_data()
        org_data = data["organizations"].get(org_id)
        if not org_data:
            raise HTTPException(404, "organization not found")
        return Organization.model_validate(org_data)


# ---------------------------------------------------------------- Member Management
@router.get("/orgs/{org_id}/members", response_model=list[OrgMember])
def list_members(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    """List members and assigned roles in the workspace."""
    with _LOCK:
        data = _load_data()
        members = data["members"].get(org_id, [])
        return [OrgMember.model_validate(m) for m in members]


@router.post("/orgs/{org_id}/members", response_model=OrgMember)
def add_member(
    org_id: str,
    req: AddMemberRequest,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Add or invite a member to the workspace with specified role (requires admin)."""
    enforce_role(auth.role, "admin")
    with _LOCK:
        data = _load_data()
        org_data = data["organizations"].get(org_id)
        if not org_data:
            raise HTTPException(404, "organization not found")

        members = data["members"].setdefault(org_id, [])
        if len(members) >= org_data["quotas"]["max_seats"]:
            raise HTTPException(403, f"seat limit of {org_data['quotas']['max_seats']} reached for this tier")

        # Check existing
        for m in members:
            if m["email"] == req.email:
                m["role"] = req.role
                _save_data(data)
                return OrgMember.model_validate(m)

        new_member = {
            "member_id": f"mem_{secrets.token_hex(4)}",
            "email": req.email,
            "role": req.role,
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }
        members.append(new_member)
        org_data["quotas"]["seats_used"] = len(members)
        _save_data(data)
        return OrgMember.model_validate(new_member)


@router.delete("/orgs/{org_id}/members/{member_id}")
def remove_member(
    org_id: str,
    member_id: str,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Remove a member from the workspace."""
    enforce_role(auth.role, "admin")
    with _LOCK:
        data = _load_data()
        members = data["members"].get(org_id, [])
        initial_len = len(members)
        data["members"][org_id] = [m for m in members if m["member_id"] != member_id]
        if len(data["members"][org_id]) == initial_len:
            raise HTTPException(404, "member not found")

        if org_id in data["organizations"]:
            data["organizations"][org_id]["quotas"]["seats_used"] = len(data["members"][org_id])
        _save_data(data)
        return {"ok": True, "removed_member_id": member_id}


# ---------------------------------------------------------------- API Key Management
@router.post("/orgs/{org_id}/keys", response_model=CreateKeyResponse)
def create_api_key(
    org_id: str,
    req: CreateKeyRequest,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Generate a new secure API key with role and scopes (returns raw token once)."""
    enforce_role(auth.role, "admin")
    key_id = f"key_{secrets.token_hex(6)}"
    raw_secret = secrets.token_hex(20)
    token = f"rw_live_{raw_secret}"
    hashed = _hash_key(token)
    prefix = token[:10]
    last4 = token[-4:]
    now = datetime.now(timezone.utc).isoformat()

    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.fromtimestamp(time.time() + req.expires_in_days * 86400, timezone.utc).isoformat()

    with _LOCK:
        data = _load_data()
        if org_id not in data["organizations"]:
            raise HTTPException(404, "organization not found")

        key_record = {
            "key_id": key_id,
            "org_id": org_id,
            "name": req.name,
            "hashed_secret": hashed,
            "prefix": prefix,
            "last4": last4,
            "role": req.role,
            "scopes": req.scopes,
            "created_at": now,
            "expires_at": expires_at,
            "is_active": True,
            "last_used_at": None,
        }
        data["api_keys"][key_id] = key_record
        _save_data(data)

    return CreateKeyResponse(
        key_id=key_id,
        name=req.name,
        token=token,
        role=req.role,
        scopes=req.scopes,
        created_at=now,
        expires_at=expires_at,
    )


@router.get("/orgs/{org_id}/keys", response_model=list[ApiKeyItem])
def list_api_keys(
    org_id: str,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """List API keys for an organization (plaintext secret is never returned)."""
    enforce_role(auth.role, "auditor")
    with _LOCK:
        data = _load_data()
        keys = [
            ApiKeyItem(
                key_id=k["key_id"],
                name=k["name"],
                prefix=k["prefix"],
                last4=k["last4"],
                role=k["role"],
                scopes=k.get("scopes", []),
                created_at=k["created_at"],
                expires_at=k.get("expires_at"),
                is_active=k.get("is_active", True),
                last_used_at=k.get("last_used_at"),
            )
            for k in data["api_keys"].values()
            if k.get("org_id") == org_id
        ]
        return keys


@router.delete("/orgs/{org_id}/keys/{key_id}")
def revoke_api_key(
    org_id: str,
    key_id: str,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Revoke an active API key immediately."""
    enforce_role(auth.role, "admin")
    with _LOCK:
        data = _load_data()
        key_data = data["api_keys"].get(key_id)
        if not key_data or key_data.get("org_id") != org_id:
            raise HTTPException(404, "API key not found")
        key_data["is_active"] = False
        _save_data(data)
        return {"ok": True, "revoked_key_id": key_id}


# ---------------------------------------------------------------- Usage & Quota Breakdown
@router.get("/orgs/{org_id}/usage")
def get_usage(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    """Retrieve detailed usage and remaining quota for the billing period."""
    with _LOCK:
        data = _load_data()
        org_data = data["organizations"].get(org_id)
        if not org_data:
            raise HTTPException(404, "organization not found")
        quotas = org_data["quotas"]
        return {
            "organization_id": org_id,
            "organization_name": org_data["name"],
            "tier": org_data["tier"],
            "checks_limit": quotas["checks_limit"],
            "checks_used": quotas["checks_used"],
            "checks_remaining": max(0, quotas["checks_limit"] - quotas["checks_used"]),
            "utilization_percent": round((quotas["checks_used"] / quotas["checks_limit"]) * 100, 2)
            if quotas["checks_limit"]
            else 0.0,
            "seats_used": quotas["seats_used"],
            "max_seats": quotas["max_seats"],
            "rate_limit_per_min": quotas["rate_limit_per_min"],
            "pdf_ingest_allowed": quotas["pdf_ingest"],
        }


@router.get("/auth/whoami")
def whoami(auth: AuthenticatedContext = Depends(get_current_auth)):
    """Inspect the current caller authentication, workspace context, and permissions."""
    return {
        "auth_type": auth.auth_type,
        "caller_id": auth.user_or_key,
        "role": auth.role,
        "scopes": auth.scopes,
        "organization": {
            "id": auth.org.id,
            "name": auth.org.name,
            "tier": auth.org.tier,
            "checks_remaining": max(0, auth.org.quotas.checks_limit - auth.org.quotas.checks_used),
        },
    }
