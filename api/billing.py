"""Pricing and custom subscriptions (Razorpay).

GET  /billing/config     -> {enabled, key_id, presets, free, limits}   (key_id is public; the secret never leaves here)
POST /billing/quote      -> line items and totals for a custom plan, computed here
POST /billing/subscribe  -> creates a Razorpay plan for exactly that amount, then a subscription; returns its id
POST /billing/verify     -> checks Razorpay's signature on the payment (HMAC-SHA256 with the key secret)

Keys come only from RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET in the environment. Without them, quotes still work and
subscribe returns 503 with a clear message. Use test keys (rzp_test_...) until the flow is verified end to end.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api import constants as C, limits

router = APIRouter()
RZP = "https://api.razorpay.com/v1"


def _keys() -> tuple[str, str] | None:
    k, s = os.environ.get("RAZORPAY_KEY_ID", "").strip(), os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    return (k, s) if k and s else None


class Plan(BaseModel):
    constituencies: int = 1
    whatsapp: bool = False
    languages: int = 0
    reviewers: int = 0
    voice_replies: int = 0
    onprem: bool = False
    nonprofit: bool = False
    annual: bool = False


def _clamp(v: int, key: str) -> int:
    lo, hi = C.PRICING_LIMITS[key]
    return max(lo, min(hi, int(v)))


def quote(p: Plan) -> dict:
    """Every number on the pricing page comes from here."""
    P = C.PRICING
    n_c, n_l = _clamp(p.constituencies, "constituencies"), _clamp(p.languages, "languages")
    n_r, n_v = _clamp(p.reviewers, "reviewers"), _clamp(p.voice_replies, "voice_replies")
    lines = [{"key": "platform", "label": P["platform"]["label"], "qty": 1, "inr": P["platform"]["inr"]},
             {"key": "constituency", "label": P["constituency"]["label"], "qty": n_c, "inr": n_c * P["constituency"]["inr"]}]
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
    return {"lines": lines, "list_monthly_inr": list_month, "nonprofit_discount": off, "monthly_inr": month,
            "period": "yearly" if p.annual else "monthly", "charge_inr": charge,
            "effective_monthly_inr": round(charge / (12 if p.annual else 1)),
            "annual_months_free": C.PRICING_DISCOUNTS["annual_months_free"] if p.annual else 0}


def _summary(p: Plan) -> str:
    return (f"{p.constituencies} constituencies, {'WhatsApp, ' if p.whatsapp else ''}{p.languages} extra languages, "
            f"{p.reviewers} reviewers, {p.voice_replies} voice replies{', on-prem' if p.onprem else ''}"
            f"{', nonprofit' if p.nonprofit else ''}")[:250]


@router.get("/billing/config")
def billing_config():
    k = _keys()
    return {"enabled": bool(k), "key_id": k[0] if k else None, "test_mode": bool(k and k[0].startswith("rzp_test_")),
            "presets": C.PRICING_PRESETS, "free": C.PRICING_FREE, "limits": C.PRICING_LIMITS, "prices": C.PRICING,
            "discounts": C.PRICING_DISCOUNTS}


@router.post("/billing/quote")
def billing_quote(p: Plan):
    return quote(p)


class Subscribe(BaseModel):
    plan: Plan
    org: str = Field("", max_length=80)  # optional organisation name, shown on the Razorpay receipt


@router.post("/billing/subscribe")
def billing_subscribe(req: Subscribe, _=Depends(limits.rate("subscribe"))):
    k = _keys()
    if not k:
        raise HTTPException(503, "payments are not set up yet: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are missing")
    q = quote(req.plan)
    auth = (k[0], k[1])
    try:
        with httpx.Client(timeout=20, auth=auth) as c:
            plan = c.post(f"{RZP}/plans", json={
                "period": q["period"], "interval": 1,
                "item": {"name": "RollWatch custom plan", "amount": int(q["charge_inr"] * 100), "currency": "INR",
                         "description": _summary(req.plan)}})
            plan.raise_for_status()
            sub = c.post(f"{RZP}/subscriptions", json={
                "plan_id": plan.json()["id"], "total_count": 1 if req.plan.annual else 12, "quantity": 1,
                "customer_notify": 1, "notes": {"plan": _summary(req.plan), "org": req.org[:80]}})
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
    return {"subscription_id": s["id"], "key_id": k[0], "charge_inr": q["charge_inr"], "period": q["period"],
            "short_url": s.get("short_url"), "status": s.get("status")}


class Verify(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str


@router.post("/billing/verify")
def billing_verify(v: Verify):
    k = _keys()
    if not k:
        raise HTTPException(503, "payments are not set up")
    msg = f"{v.razorpay_payment_id}|{v.razorpay_subscription_id}".encode("utf-8")
    want = hmac.new(k[1].encode("utf-8"), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, v.razorpay_signature):
        raise HTTPException(400, "signature does not match")
    return {"verified": True, "subscription_id": v.razorpay_subscription_id}
