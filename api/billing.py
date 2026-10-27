"""Pricing, custom subscriptions and signed webhook event persistence (Razorpay).

GET  /billing/config                    -> {enabled, key_id, presets, free, limits}
POST /billing/quote                     -> line items and totals for a custom plan
POST /billing/subscribe                 -> creates a Razorpay plan and subscription; persists subscription
POST /billing/verify                    -> checks payment signature, transitions subscription to authenticated
POST /billing/webhook                   -> signed Razorpay webhook handler, persists events with HMAC-SHA256
GET  /billing/events                    -> list of persisted webhook events
GET  /billing/subscriptions             -> list of tracked subscriptions
GET  /billing/subscriptions/{sub_id}    -> subscription status, lifecycle state and entitlements
POST /billing/subscriptions/{sub_id}/cancel -> cancel subscription (immediate or at cycle end)
GET  /billing/subscriptions/{sub_id}/quotas -> active resource quotas based on lifecycle state

Keys come from RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET / RAZORPAY_WEBHOOK_SECRET.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api import constants as C, limits

log = logging.getLogger("rollwatch.billing")
router = APIRouter()
RZP = "https://api.razorpay.com/v1"
ROOT = Path(__file__).resolve().parent.parent

_LOCK = threading.RLock()


def _data_dir() -> Path:
    d = Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _events_path() -> Path:
    return _data_dir() / "billing_events.jsonl"


def _subs_path() -> Path:
    return _data_dir() / "subscriptions.json"


def _keys() -> tuple[str, str] | None:
    k = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    s = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    return (k, s) if k and s else None


def _webhook_secret() -> str:
    return os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip() or (os.environ.get("RAZORPAY_KEY_SECRET", "").strip())


class Plan(BaseModel):
    constituencies: int = 1
    whatsapp: bool = False
    languages: int = 0
    reviewers: int = 0
    voice_replies: int = 0
    onprem: bool = False
    nonprofit: bool = False
    annual: bool = False


class SubscriptionRecord(BaseModel):
    id: str
    org: str = ""
    plan: Plan
    status: str = "created"  # created, authenticated, active, pending, halted, cancelled, completed, expired
    charge_inr: float
    period: str = "monthly"
    created_at: float
    updated_at: float
    current_start: float | None = None
    current_end: float | None = None
    payments_count: int = 0
    last_payment_id: str | None = None
    short_url: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)


# In-memory subscription store backed by artifacts/subscriptions.json
_SUBSCRIPTIONS: dict[str, SubscriptionRecord] = {}


def _load_subscriptions():
    global _SUBSCRIPTIONS
    p = _subs_path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            with _LOCK:
                _SUBSCRIPTIONS = {k: SubscriptionRecord.model_validate(v) for k, v in data.items()}
        except Exception as e:
            log.warning("Failed to load subscriptions from %s: %s", p, e)


def _save_subscriptions():
    p = _subs_path()
    try:
        with _LOCK:
            data = {k: v.model_dump() for k, v in _SUBSCRIPTIONS.items()}
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("Failed to save subscriptions to %s: %s", p, e)


_load_subscriptions()


def _clamp(v: int, key: str) -> int:
    lo, hi = C.PRICING_LIMITS[key]
    return max(lo, min(hi, int(v)))


def quote(p: Plan) -> dict:
    """Every number on the pricing page comes from here."""
    P = C.PRICING
    n_c, n_l = _clamp(p.constituencies, "constituencies"), _clamp(p.languages, "languages")
    n_r, n_v = _clamp(p.reviewers, "reviewers"), _clamp(p.voice_replies, "voice_replies")
    lines = [
        {"key": "platform", "label": P["platform"]["label"], "qty": 1, "inr": P["platform"]["inr"]},
        {"key": "constituency", "label": P["constituency"]["label"], "qty": n_c, "inr": n_c * P["constituency"]["inr"]},
    ]
    if p.whatsapp:
        lines.append({"key": "whatsapp", "label": P["whatsapp"]["label"], "qty": 1, "inr": P["whatsapp"]["inr"]})
    if n_l:
        lines.append({"key": "language", "label": P["language"]["label"], "qty": n_l, "inr": n_l * P["language"]["inr"]})
    if n_r:
        lines.append({"key": "reviewer", "label": P["reviewer"]["label"], "qty": n_r, "inr": n_r * P["reviewer"]["inr"]})
    if n_v:
        lines.append({"key": "voice", "label": P["voice"]["label"], "qty": n_v, "inr": round(n_v * P["voice"]["inr"])})
    if p.onprem:
        lines.append({"key": "onprem", "label": P["onprem"]["label"], "qty": 1, "inr": P["onprem"]["inr"]})
    list_month = sum(x["inr"] for x in lines)
    off = C.PRICING_DISCOUNTS["nonprofit_off"] if p.nonprofit else 0.0
    month = round(list_month * (1 - off))
    months_billed = 12 - C.PRICING_DISCOUNTS["annual_months_free"] if p.annual else 1
    charge = month * months_billed
    return {
        "lines": lines,
        "list_monthly_inr": list_month,
        "nonprofit_discount": off,
        "monthly_inr": month,
        "period": "yearly" if p.annual else "monthly",
        "charge_inr": charge,
        "effective_monthly_inr": round(charge / (12 if p.annual else 1)),
        "annual_months_free": C.PRICING_DISCOUNTS["annual_months_free"] if p.annual else 0,
    }


def _summary(p: Plan) -> str:
    return (
        f"{p.constituencies} constituencies, {'WhatsApp, ' if p.whatsapp else ''}{p.languages} extra languages, "
        f"{p.reviewers} reviewers, {p.voice_replies} voice replies{', on-prem' if p.onprem else ''}"
        f"{', nonprofit' if p.nonprofit else ''}"
    )[:250]


def _persist_event(event_dict: dict[str, Any]):
    """Persist signed webhook event to durable log with timestamp and checksum."""
    line = json.dumps(event_dict, ensure_ascii=False)
    p = _events_path()
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        log.warning("Failed to append event to %s: %s", p, e)


def _compute_quotas(sub: SubscriptionRecord) -> dict[str, Any]:
    """Derives live active quotas and entitlements from the subscription lifecycle state."""
    active = sub.status in ("authenticated", "active", "charged")
    p = sub.plan
    if not active:
        # Revert to standard free tier
        return {
            "tier": "free",
            "status": sub.status,
            "constituencies_allowed": 1,
            "whatsapp_enabled": False,
            "languages_allowed": ["en", "hi", "pa"],
            "reviewers_allowed": 1,
            "voice_replies_monthly": 0,
            "onprem_license": False,
            "expires_at": sub.current_end,
        }
    return {
        "tier": "custom_paid",
        "status": sub.status,
        "constituencies_allowed": p.constituencies,
        "whatsapp_enabled": p.whatsapp,
        "languages_allowed": ["en", "hi", "pa"] + ([f"lang_{i+1}" for i in range(p.languages)] if p.languages else []),
        "reviewers_allowed": max(1, p.reviewers),
        "voice_replies_monthly": p.voice_replies,
        "onprem_license": p.onprem,
        "current_period_end": sub.current_end,
        "billing_period": sub.period,
    }


@router.get("/billing/config")
def billing_config():
    k = _keys()
    return {
        "enabled": bool(k),
        "key_id": k[0] if k else None,
        "test_mode": bool(k and k[0].startswith("rzp_test_")),
        "presets": C.PRICING_PRESETS,
        "free": C.PRICING_FREE,
        "limits": C.PRICING_LIMITS,
        "prices": C.PRICING,
        "discounts": C.PRICING_DISCOUNTS,
    }


@router.post("/billing/quote")
def billing_quote(p: Plan):
    return quote(p)


class Subscribe(BaseModel):
    plan: Plan
    org: str = Field("", max_length=80)  # optional organisation name


@router.post("/billing/subscribe")
def billing_subscribe(req: Subscribe, _=Depends(limits.rate("subscribe"))):
    k = _keys()
    if not k:
        # In test/demo without keys, generate a synthetic mock subscription ID
        now = time.time()
        sub_id = f"sub_sim_{int(now)}_{os.urandom(4).hex()}"
        q = quote(req.plan)
        rec = SubscriptionRecord(
            id=sub_id,
            org=req.org[:80],
            plan=req.plan,
            status="created",
            charge_inr=q["charge_inr"],
            period=q["period"],
            created_at=now,
            updated_at=now,
            short_url=f"https://rzp.io/i/sim_{sub_id}",
        )
        with _LOCK:
            _SUBSCRIPTIONS[sub_id] = rec
        _save_subscriptions()
        return {
            "subscription_id": sub_id,
            "key_id": "rzp_test_simulated",
            "charge_inr": q["charge_inr"],
            "period": q["period"],
            "short_url": rec.short_url,
            "status": "created",
            "simulated": True,
        }

    q = quote(req.plan)
    auth = (k[0], k[1])
    try:
        with httpx.Client(timeout=20, auth=auth) as c:
            plan = c.post(
                f"{RZP}/plans",
                json={
                    "period": q["period"],
                    "interval": 1,
                    "item": {
                        "name": "RollWatch custom plan",
                        "amount": int(q["charge_inr"] * 100),
                        "currency": "INR",
                        "description": _summary(req.plan),
                    },
                },
            )
            plan.raise_for_status()
            sub = c.post(
                f"{RZP}/subscriptions",
                json={
                    "plan_id": plan.json()["id"],
                    "total_count": 1 if req.plan.annual else 12,
                    "quantity": 1,
                    "customer_notify": 1,
                    "notes": {"plan": _summary(req.plan), "org": req.org[:80]},
                },
            )
            sub.raise_for_status()
    except httpx.HTTPStatusError as e:
        msg = ""
        try:
            msg = e.response.json().get("error", {}).get("description", "")
        except ValueError:
            pass
        raise HTTPException(502, f"Razorpay refused the request: {msg or e.response.status_code}")
    except httpx.HTTPError:
        raise HTTPException(502, "Razorpay is not reachable right now")

    s = sub.json()
    now = time.time()
    sub_id = s["id"]
    rec = SubscriptionRecord(
        id=sub_id,
        org=req.org[:80],
        plan=req.plan,
        status=s.get("status", "created"),
        charge_inr=q["charge_inr"],
        period=q["period"],
        created_at=now,
        updated_at=now,
        short_url=s.get("short_url"),
    )
    with _LOCK:
        _SUBSCRIPTIONS[sub_id] = rec
    _save_subscriptions()

    return {
        "subscription_id": s["id"],
        "key_id": k[0],
        "charge_inr": q["charge_inr"],
        "period": q["period"],
        "short_url": s.get("short_url"),
        "status": s.get("status"),
    }


class Verify(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str


@router.post("/billing/verify")
def billing_verify(v: Verify):
    k = _keys()
    # Check simulated subscriptions if keys not set
    if not k:
        if v.razorpay_subscription_id.startswith("sub_sim_"):
            with _LOCK:
                sub = _SUBSCRIPTIONS.get(v.razorpay_subscription_id)
                if sub:
                    sub.status = "authenticated"
                    sub.last_payment_id = v.razorpay_payment_id
                    sub.updated_at = time.time()
                    sub.payments_count += 1
                    _save_subscriptions()
            return {"verified": True, "subscription_id": v.razorpay_subscription_id, "simulated": True}
        raise HTTPException(503, "payments are not set up")

    msg = f"{v.razorpay_payment_id}|{v.razorpay_subscription_id}".encode("utf-8")
    want = hmac.new(k[1].encode("utf-8"), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, v.razorpay_signature):
        raise HTTPException(400, "signature does not match")

    with _LOCK:
        sub = _SUBSCRIPTIONS.get(v.razorpay_subscription_id)
        if sub:
            sub.status = "authenticated"
            sub.last_payment_id = v.razorpay_payment_id
            sub.updated_at = time.time()
            sub.payments_count += 1
            _save_subscriptions()

    return {"verified": True, "subscription_id": v.razorpay_subscription_id}


# ------------------------------------------------------------------ Webhook & Lifecycle
@router.post("/billing/webhook")
def billing_webhook(payload: dict[str, Any], x_razorpay_signature: str | None = Header(None)):
    """Receives, verifies, and persists Razorpay webhook events with HMAC-SHA256 signature."""
    raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    secret = _webhook_secret()

    if not secret:
        # If no secret is configured, require developer or test mode
        if os.environ.get("DEMO_MODE", "0") != "1" and not os.environ.get("ALLOW_UNSIGNED_WEBHOOKS"):
            raise HTTPException(503, "webhook verification secret not configured")
    else:
        if not x_razorpay_signature:
            raise HTTPException(400, "missing X-Razorpay-Signature header")
        want1 = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        want2 = hmac.new(secret.encode("utf-8"), json.dumps(payload, ensure_ascii=False).encode("utf-8"), hashlib.sha256).hexdigest()
        if not (hmac.compare_digest(want1, x_razorpay_signature) or hmac.compare_digest(want2, x_razorpay_signature)):
            raise HTTPException(400, "invalid webhook signature")

    event_name = payload.get("event", "unknown")
    event_id = payload.get("id") or hashlib.sha256(raw_body).hexdigest()[:16]
    now = time.time()

    event_record = {
        "event_id": event_id,
        "event": event_name,
        "received_at": now,
        "payload": payload,
    }
    _persist_event(event_record)

    # Process lifecycle state changes based on event
    entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
    sub_id = entity.get("id")

    if sub_id:
        with _LOCK:
            sub = _SUBSCRIPTIONS.get(sub_id)
            if not sub:
                # If subscription was created externally, initialize record
                notes = entity.get("notes", {})
                sub = SubscriptionRecord(
                    id=sub_id,
                    org=notes.get("org", ""),
                    plan=Plan(),
                    status=entity.get("status", "created"),
                    charge_inr=float(entity.get("charge_at", 0)) / 100 if entity.get("charge_at") else 0.0,
                    created_at=now,
                    updated_at=now,
                )
                _SUBSCRIPTIONS[sub_id] = sub

            # Lifecycle transitions
            prev_status = sub.status
            if event_name == "subscription.authenticated":
                sub.status = "authenticated"
            elif event_name in ("subscription.activated", "subscription.charged"):
                sub.status = "active"
                if "current_start" in entity:
                    sub.current_start = float(entity["current_start"])
                if "current_end" in entity:
                    sub.current_end = float(entity["current_end"])
                sub.payments_count = entity.get("paid_count", sub.payments_count + 1)
            elif event_name == "subscription.pending":
                sub.status = "pending"
            elif event_name == "subscription.halted":
                sub.status = "halted"
            elif event_name == "subscription.cancelled":
                sub.status = "cancelled"
            elif event_name == "subscription.completed":
                sub.status = "completed"

            sub.updated_at = now
            sub.events.append({
                "event": event_name,
                "timestamp": now,
                "from_status": prev_status,
                "to_status": sub.status,
            })
            _save_subscriptions()

    return {"status": "ok", "event_id": event_id, "event": event_name}


@router.get("/billing/events")
def billing_events(limit: int = Query(50, ge=1, le=200)):
    """List persisted signed webhook events."""
    p = _events_path()
    if not p.exists():
        return {"events": [], "count": 0}
    events = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    except Exception as e:
        log.warning("Failed to read events from %s: %s", p, e)
    return {"events": events[-limit:], "total": len(events)}


@router.get("/billing/subscriptions")
def list_subscriptions(org: str | None = None):
    with _LOCK:
        subs = list(_SUBSCRIPTIONS.values())
    if org:
        subs = [s for s in subs if s.org.lower() == org.lower()]
    return {"subscriptions": [s.model_dump() for s in subs], "count": len(subs)}


@router.get("/billing/subscriptions/{sub_id}")
def get_subscription(sub_id: str):
    with _LOCK:
        sub = _SUBSCRIPTIONS.get(sub_id)
    if not sub:
        raise HTTPException(404, "subscription not found")
    return {"subscription": sub.model_dump(), "quotas": _compute_quotas(sub)}


@router.get("/billing/subscriptions/{sub_id}/quotas")
def get_subscription_quotas(sub_id: str):
    with _LOCK:
        sub = _SUBSCRIPTIONS.get(sub_id)
    if not sub:
        raise HTTPException(404, "subscription not found")
    return _compute_quotas(sub)


class CancelRequest(BaseModel):
    cancel_at_cycle_end: bool = True


@router.post("/billing/subscriptions/{sub_id}/cancel")
def cancel_subscription(sub_id: str, req: CancelRequest = CancelRequest()):
    with _LOCK:
        sub = _SUBSCRIPTIONS.get(sub_id)
        if not sub:
            raise HTTPException(404, "subscription not found")

    k = _keys()
    if k and not sub_id.startswith("sub_sim_"):
        auth = (k[0], k[1])
        try:
            with httpx.Client(timeout=20, auth=auth) as c:
                resp = c.post(
                    f"{RZP}/subscriptions/{sub_id}/cancel",
                    json={"cancel_at_cycle_end": int(req.cancel_at_cycle_end)},
                )
                resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Razorpay cancel failed: {e}")

    with _LOCK:
        sub.status = "cancelled"
        sub.updated_at = time.time()
        sub.events.append({
            "event": "manual_cancellation",
            "timestamp": time.time(),
            "cancel_at_cycle_end": req.cancel_at_cycle_end,
        })
        _save_subscriptions()

    return {"ok": True, "subscription_id": sub_id, "status": "cancelled"}
