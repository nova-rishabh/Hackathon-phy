"""Organization workspaces, role-based access control (RBAC), quotas, and API key management."""
from __future__ import annotations

import hashlib
import hmac
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
from api import limits, wa_auth
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
# Who is calling, and what role they hold in a *specific* organisation. Roles come only from:
#   - an API key: its own role, in its own organisation only;
#   - a signed-in user (WhatsApp code -> Bearer token): their membership in that organisation (member id = phone);
#   - the operator (X-WA-Secret): owner of every organisation, for support;
# Anonymous callers hold no role anywhere.
class AuthenticatedContext:
    def __init__(self, auth_type: str, user_or_key: str, key_org_id: str | None = None,
                 key_role: OrgRole | None = None, scopes: list[str] | None = None):
        self.auth_type = auth_type          # "api_key" | "bearer" | "operator" | "anonymous"
        self.user_or_key = user_or_key      # key id, phone number, "operator" or "anonymous"
        self.key_org_id = key_org_id
        self.key_role = key_role
        self.scopes = scopes or []


def get_current_auth(
    x_api_key: str | None = Security(API_KEY_HEADER),
    authorization: str | None = Header(None),
    x_wa_secret: str | None = Header(None),
) -> AuthenticatedContext:
    """Resolve the caller. Never grants a role by default."""
    if x_wa_secret:
        wa_auth._check_worker(x_wa_secret)  # 403 unless it is the real operator secret
        return AuthenticatedContext("operator", "operator", scopes=["*"])
    if x_api_key:
        hashed = _hash_key(x_api_key)
        with _LOCK:
            data = _load_data()
            for kdata in data["api_keys"].values():
                if hmac.compare_digest(kdata.get("hashed_secret", ""), hashed) and kdata.get("is_active", True):
                    exp = kdata.get("expires_at")
                    if exp and datetime.fromisoformat(exp) < datetime.now(timezone.utc):
                        raise HTTPException(401, "API key expired")
                    kdata["last_used_at"] = datetime.now(timezone.utc).isoformat()
                    _save_data(data)
                    return AuthenticatedContext("api_key", kdata["key_id"], kdata["org_id"], kdata["role"],
                                                kdata.get("scopes", []))
        raise HTTPException(401, "invalid or revoked API key")
    tok = (authorization or "").removeprefix("Bearer ").strip()
    user_id = wa_auth.read_token(tok) if tok else None
    if tok and not user_id:
        raise HTTPException(401, "sign in again")
    if user_id:
        return AuthenticatedContext("bearer", user_id, scopes=["*"])
    return AuthenticatedContext("anonymous", "anonymous")


def role_in(auth: AuthenticatedContext, org_id: str, data: dict[str, Any]) -> OrgRole | None:
    if auth.auth_type == "operator":
        return "owner"
    if auth.auth_type == "api_key":
        return auth.key_role if auth.key_org_id == org_id else None
    if auth.auth_type == "bearer":
        for m in data["members"].get(org_id, []):
            if m.get("email") == auth.user_or_key:
                return m.get("role")
    return None


def require_role(auth: AuthenticatedContext, org_id: str, needed: OrgRole, data: dict[str, Any]) -> OrgRole:
    """404 if the organisation doesn't exist or the caller isn't in it (no leaking which ids exist); 403 if the
    caller is in it but below the needed role."""
    if org_id not in data["organizations"]:
        raise HTTPException(404, "organization not found")
    role = role_in(auth, org_id, data)
    if role is None:
        if auth.auth_type == "anonymous":
            raise HTTPException(401, "sign in or send an API key")
        raise HTTPException(404, "organization not found")
    enforce_role(role, needed)
    return role


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


def _not_above(granted: OrgRole, mine: OrgRole):
    """Nobody can hand out a role higher than their own."""
    if ROLE_HIERARCHY.get(granted, 0) > ROLE_HIERARCHY.get(mine, 0):
        raise HTTPException(403, f"you can't grant {granted}: your role is {mine}")


# ---------------------------------------------------------------- Workspace Endpoints
@router.post("/orgs", response_model=Organization)
def create_organization(
    req: CreateOrgRequest,
    auth: AuthenticatedContext = Depends(get_current_auth),
    _=Depends(limits.rate("orgs")),
):
    """Create a workspace. The signed-in caller becomes its owner. New workspaces start on the free tier; paid
    tiers come through billing (only the operator can set a tier directly)."""
    if auth.auth_type not in ("bearer", "operator"):
        raise HTTPException(401, "sign in to create a workspace")
    tier: OrgTier = req.tier if auth.auth_type == "operator" else "free"
    owner = req.admin_email if auth.auth_type == "operator" else auth.user_or_key
    slug = (req.slug or req.name).lower().replace(" ", "-").replace("_", "-")[:60]
    org_id = f"org_{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc).isoformat()
    new_org = Organization(id=org_id, name=req.name[:120], slug=slug, tier=tier,
                           quotas=TIER_QUOTAS[tier].model_copy(), created_at=now)
    with _LOCK:
        data = _load_data()
        data["organizations"][org_id] = new_org.model_dump()
        data["members"][org_id] = [{"member_id": f"mem_{secrets.token_hex(4)}", "email": owner,
                                    "role": "owner", "joined_at": now}]
        _save_data(data)
    return new_org


@router.get("/orgs", response_model=list[Organization])
def list_organizations(auth: AuthenticatedContext = Depends(get_current_auth)):
    """The workspaces the caller belongs to (all of them for the operator)."""
    if auth.auth_type == "anonymous":
        raise HTTPException(401, "sign in or send an API key")
    with _LOCK:
        data = _load_data()
        return [Organization.model_validate(v) for k, v in data["organizations"].items() if role_in(auth, k, data)]


@router.get("/orgs/{org_id}", response_model=Organization)
def get_organization(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    with _LOCK:
        data = _load_data()
        require_role(auth, org_id, "viewer", data)
        return Organization.model_validate(data["organizations"][org_id])


# ---------------------------------------------------------------- Member Management
@router.get("/orgs/{org_id}/members", response_model=list[OrgMember])
def list_members(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    with _LOCK:
        data = _load_data()
        require_role(auth, org_id, "viewer", data)
        return [OrgMember.model_validate(m) for m in data["members"].get(org_id, [])]


@router.post("/orgs/{org_id}/members", response_model=OrgMember)
def add_member(
    org_id: str,
    req: AddMemberRequest,
    auth: AuthenticatedContext = Depends(get_current_auth),
):
    """Add a member, or change an existing member's role (admin or above, never above your own role)."""
    with _LOCK:
        data = _load_data()
        mine = require_role(auth, org_id, "admin", data)
        _not_above(req.role, mine)
        org_data = data["organizations"][org_id]
        members = data["members"].setdefault(org_id, [])
        for m in members:
            if m["email"] == req.email:
                _not_above(m["role"], mine)  # can't demote someone who outranks you
                m["role"] = req.role
                _save_data(data)
                return OrgMember.model_validate(m)
        if len(members) >= org_data["quotas"]["max_seats"]:
            raise HTTPException(403, f"seat limit of {org_data['quotas']['max_seats']} reached for this tier")
        new_member = {"member_id": f"mem_{secrets.token_hex(4)}", "email": req.email[:120], "role": req.role,
                      "joined_at": datetime.now(timezone.utc).isoformat()}
        members.append(new_member)
        org_data["quotas"]["seats_used"] = len(members)
        _save_data(data)
        return OrgMember.model_validate(new_member)


@router.delete("/orgs/{org_id}/members/{member_id}")
def remove_member(org_id: str, member_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    with _LOCK:
        data = _load_data()
        mine = require_role(auth, org_id, "admin", data)
        members = data["members"].get(org_id, [])
        target = next((m for m in members if m["member_id"] == member_id), None)
        if target is None:
            raise HTTPException(404, "member not found")
        _not_above(target["role"], mine)
        if target["role"] == "owner" and sum(m["role"] == "owner" for m in members) == 1:
            raise HTTPException(409, "a workspace needs at least one owner")
        data["members"][org_id] = [m for m in members if m["member_id"] != member_id]
        data["organizations"][org_id]["quotas"]["seats_used"] = len(data["members"][org_id])
        _save_data(data)
        return {"ok": True, "removed_member_id": member_id}


# ---------------------------------------------------------------- API Key Management
@router.post("/orgs/{org_id}/keys", response_model=CreateKeyResponse)
def create_api_key(org_id: str, req: CreateKeyRequest, auth: AuthenticatedContext = Depends(get_current_auth)):
    """Create an API key for this workspace (admin or above; the key's role can't exceed yours)."""
    with _LOCK:
        data = _load_data()
        mine = require_role(auth, org_id, "admin", data)
        _not_above(req.role, mine)
        key_id = f"key_{secrets.token_hex(6)}"
        token = f"rw_live_{secrets.token_hex(20)}"
        now = datetime.now(timezone.utc).isoformat()
        days = min(req.expires_in_days or 90, 365)  # keys always expire
        expires_at = datetime.fromtimestamp(time.time() + days * 86400, timezone.utc).isoformat()
        data["api_keys"][key_id] = {
            "key_id": key_id, "org_id": org_id, "name": req.name[:80], "hashed_secret": _hash_key(token),
            "prefix": token[:10], "last4": token[-4:], "role": req.role, "scopes": req.scopes,
            "created_at": now, "expires_at": expires_at, "is_active": True, "last_used_at": None,
        }
        _save_data(data)
    return CreateKeyResponse(key_id=key_id, name=req.name, token=token, role=req.role, scopes=req.scopes,
                             created_at=now, expires_at=expires_at)


@router.get("/orgs/{org_id}/keys", response_model=list[ApiKeyItem])
def list_api_keys(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    """List this workspace's API keys (the secret itself is never returned)."""
    with _LOCK:
        data = _load_data()
        require_role(auth, org_id, "auditor", data)
        return [
            ApiKeyItem(key_id=k["key_id"], name=k["name"], prefix=k["prefix"], last4=k["last4"], role=k["role"],
                       scopes=k.get("scopes", []), created_at=k["created_at"], expires_at=k.get("expires_at"),
                       is_active=k.get("is_active", True), last_used_at=k.get("last_used_at"))
            for k in data["api_keys"].values() if k.get("org_id") == org_id
        ]


@router.delete("/orgs/{org_id}/keys/{key_id}")
def revoke_api_key(org_id: str, key_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    with _LOCK:
        data = _load_data()
        require_role(auth, org_id, "admin", data)
        key_data = data["api_keys"].get(key_id)
        if not key_data or key_data.get("org_id") != org_id:
            raise HTTPException(404, "API key not found")
        key_data["is_active"] = False
        _save_data(data)
        return {"ok": True, "revoked_key_id": key_id}


# ---------------------------------------------------------------- Usage & Quota Breakdown
@router.get("/orgs/{org_id}/usage")
def get_usage(org_id: str, auth: AuthenticatedContext = Depends(get_current_auth)):
    with _LOCK:
        data = _load_data()
        require_role(auth, org_id, "viewer", data)
        org_data = data["organizations"][org_id]
        quotas = org_data["quotas"]
        return {
            "organization_id": org_id,
            "organization_name": org_data["name"],
            "tier": org_data["tier"],
            "checks_limit": quotas["checks_limit"],
            "checks_used": quotas["checks_used"],
            "checks_remaining": max(0, quotas["checks_limit"] - quotas["checks_used"]),
            "utilization_percent": round((quotas["checks_used"] / quotas["checks_limit"]) * 100, 2)
            if quotas["checks_limit"] else 0.0,
            "seats_used": quotas["seats_used"],
            "max_seats": quotas["max_seats"],
            "rate_limit_per_min": quotas["rate_limit_per_min"],
            "pdf_ingest_allowed": quotas["pdf_ingest"],
        }


@router.get("/auth/whoami")
def whoami(auth: AuthenticatedContext = Depends(get_current_auth)):
    """Who the caller is, and their role in each workspace they belong to."""
    with _LOCK:
        data = _load_data()
        orgs = [{"id": k, "name": v["name"], "tier": v["tier"], "role": role_in(auth, k, data),
                 "checks_remaining": max(0, v["quotas"]["checks_limit"] - v["quotas"]["checks_used"])}
                for k, v in data["organizations"].items() if role_in(auth, k, data)]
    caller = wa_auth.mask(auth.user_or_key) if auth.auth_type == "bearer" else auth.user_or_key
    first = orgs[0] if orgs else None
    return {"auth_type": auth.auth_type, "caller_id": caller,
            "role": auth.key_role if auth.auth_type == "api_key" else (first or {}).get("role"),
            "scopes": auth.scopes, "organization": first, "organizations": orgs}
