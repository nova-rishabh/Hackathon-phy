"""WhatsApp sign-in (6-digit code), account data and the WhatsApp worker bridge.

The WhatsApp Web session runs in wa/worker.js on a laptop that only makes OUTBOUND calls here:
it long-polls /wa/outbox, heartbeats, and forwards inbound chats to /wa/inbound. This API owns the
codes, tokens and account rows. Codes are stored only as sha256(mobile+code+AUTH_SECRET).
Never logged: codes, tokens, full phone numbers, secrets (ops.jsonl records the route path only).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from collections import deque

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api import constants as C

log = logging.getLogger("rollwatch.wa")
router = APIRouter()

AUTH_SECRET = os.environ.get("AUTH_SECRET") or ""
if not AUTH_SECRET:
    AUTH_SECRET = secrets.token_hex(32)
    log.warning("AUTH_SECRET not set: using a random key; sign-in tokens end when the API restarts.")
_KEY = AUTH_SECRET.encode("utf-8")
CODE_TTL = 300
MAX_ATTEMPTS = 5
TOKEN_TTL = 7 * 24 * 3600
HEARTBEAT_TTL = 45


def _err(status: int, **body) -> JSONResponse:
    return JSONResponse(status_code=status, content=body)


# ------------------------------------------------------------------ phone helpers
def normalize(mobile: str) -> str | None:
    """E.164. Ten digits -> +91. Leading 0 / 91 handled. None when invalid."""
    s = re.sub(r"[\s\-().]", "", mobile or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    if s.startswith("+"):
        d = s[1:]
    else:
        d = s.lstrip("0") if len(s) == 11 and s.startswith("0") else s
        if len(d) == 10:
            d = "91" + d
    if not d.isdigit() or not 8 <= len(d) <= 15 or d.startswith("0"):
        return None
    if d.startswith("91") and (len(d) != 12 or d[2] not in "6789"):
        return None
    return "+" + d


def mask(e164: str) -> str:
    """+919876541234 -> '+91 ••••• 41234'."""
    d = e164.lstrip("+")
    cc = "91" if d.startswith("91") and len(d) == 12 else d[: max(1, len(d) - 10)]
    return f"+{cc} ••••• {d[-5:]}"


# ------------------------------------------------------------------ rate limits (in memory)
_hits: dict[str, deque] = {}


def _limit(key: str, n: int, window: int, now: float) -> int:
    """0 when allowed (and recorded by the caller), else seconds to wait."""
    q = _hits.setdefault(key, deque())
    while q and now - q[0] >= window:
        q.popleft()
    return int(window - (now - q[0])) + 1 if len(q) >= n else 0


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


# ------------------------------------------------------------------ worker state + outbox
_worker = {"state": "offline", "seen": 0.0, "number": None}
_outbox: list[dict] = []
_outbox_evt: asyncio.Event | None = None


def _evt() -> asyncio.Event:
    global _outbox_evt
    if _outbox_evt is None:
        _outbox_evt = asyncio.Event()
    return _outbox_evt


def _worker_online() -> bool:
    return time.time() - _worker["seen"] < HEARTBEAT_TTL


def _beat(state: str | None = None, number: str | None = None):
    _worker["seen"] = time.time()
    if state:
        _worker["state"] = state
    if number is not None:
        _worker["number"] = number


def _check_worker(secret: str | None):
    want = os.environ.get("WA_WORKER_SECRET")
    if not want:
        raise HTTPException(503, "WA_WORKER_SECRET is not set: worker endpoints are disabled")
    if not secret or not hmac.compare_digest(secret.encode("utf-8"), want.encode("utf-8")):
        raise HTTPException(403, "bad worker secret")


# ------------------------------------------------------------------ codes + tokens
_pending: dict[str, dict] = {}  # mobile -> {"h", "exp", "left"}


def _code_hash(mobile: str, code: str) -> str:
    return hashlib.sha256((mobile + code + AUTH_SECRET).encode("utf-8")).hexdigest()


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_token(mobile: str) -> str:
    body = _b64(json.dumps({"sub": mobile, "exp": int(time.time()) + TOKEN_TTL}, separators=(",", ":")).encode())
    return body + "." + _b64(hmac.new(_KEY, body.encode("ascii"), hashlib.sha256).digest())


def read_token(token: str) -> str | None:
    try:
        body, sig = token.split(".")
        want = _b64(hmac.new(_KEY, body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, want):
            return None
        p = json.loads(_unb64(body))
        return p["sub"] if int(p["exp"]) > time.time() else None
    except Exception:
        return None


def _user(authorization: str | None) -> str:
    tok = (authorization or "").removeprefix("Bearer ").strip()
    sub = read_token(tok) if tok else None
    if not sub:
        raise HTTPException(401, "sign in again")
    return sub


class StartReq(BaseModel):
    mobile: str


class VerifyReq(BaseModel):
    mobile: str
    code: str


@router.post("/auth/wa/start")
async def wa_start(req: StartReq, request: Request):
    m = normalize(req.mobile)
    if not m:
        raise HTTPException(422, "enter a valid mobile number")
    now = time.time()
    keys = [(f"n60:{m}", 1, 60), (f"nh:{m}", 5, 3600), (f"ip:{_client_ip(request)}", 30, 900)]
    wait = max(_limit(k, n, w, now) for k, n, w in keys)
    if wait:
        return _err(429, error="rate_limited", retry_in=wait)
    if not _worker_online():
        return _err(503, error="sender_offline")
    for k, _, _ in keys:
        _hits[k].append(now)
    code = f"{secrets.randbelow(10 ** 6):06d}"
    _pending[m] = {"h": _code_hash(m, code), "exp": now + CODE_TTL, "left": MAX_ATTEMPTS}
    _outbox.append({"id": secrets.token_hex(8), "to": m, "text": C.WA_OTP_TEXT["en"].format(code=code)})
    _evt().set()
    return {"sent": True, "to": mask(m), "expires_in": CODE_TTL}


@router.post("/auth/wa/verify")
async def wa_verify(req: VerifyReq):
    m = normalize(req.mobile)
    p = _pending.get(m or "")
    if not p:
        return _err(410, error="expired")
    if time.time() > p["exp"] or p["left"] <= 0:
        _pending.pop(m, None)
        return _err(410, error="expired")
    code = re.sub(r"\D", "", req.code or "")
    if not hmac.compare_digest(_code_hash(m, code), p["h"]):
        p["left"] -= 1
        if p["left"] <= 0:
            _pending.pop(m, None)
        return _err(401, error="wrong_code", attempts_left=max(p["left"], 0))
    _pending.pop(m, None)
    return {"token": make_token(m), "user": {"mobile_masked": mask(m)}}


@router.get("/auth/me")
async def auth_me(authorization: str | None = Header(None)):
    return {"mobile_masked": mask(_user(authorization))}


# ------------------------------------------------------------------ account store (Supabase REST or memory)
class _Store:
    def __init__(self):
        self.url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
        self.kind = "supabase" if self.url and self.key else "memory"
        self.mem: dict[str, dict[str, dict]] = {}
        if self.kind == "memory":
            log.warning("SUPABASE_SERVICE_ROLE_KEY not set: account data is kept in memory only.")

    def _h(self, extra: dict | None = None) -> dict:
        return {"apikey": self.key, "Authorization": f"Bearer {self.key}", **(extra or {})}

    async def list(self, table: str, phone: str) -> list[dict]:
        if self.kind == "memory":
            rows = [r for (t, _), r in self.mem.get(phone, {}).items() if t == table]
            return sorted(rows, key=lambda r: r["created_at"], reverse=True)
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{self.url}/rest/v1/{table}", headers=self._h(),
                            params={"phone": f"eq.{phone}", "order": "created_at.desc", "select": "*"})
        r.raise_for_status()
        return [{k: v for k, v in x.items() if k != "phone"} for x in r.json()]

    async def put(self, table: str, phone: str, key: str, row: dict):
        if self.kind == "memory":
            row = {**row, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            self.mem.setdefault(phone, {})[(table, row[key])] = row
            return
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{self.url}/rest/v1/{table}", json={**row, "phone": phone},
                             headers=self._h({"Prefer": "resolution=merge-duplicates,return=minimal"}))
        r.raise_for_status()

    async def delete(self, table: str, phone: str, key: str, val: str):
        if self.kind == "memory":
            self.mem.get(phone, {}).pop((table, val), None)
            return
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.delete(f"{self.url}/rest/v1/{table}", headers=self._h(),
                               params={"phone": f"eq.{phone}", key: f"eq.{val}"})
        r.raise_for_status()


_store: _Store | None = None


def account() -> _Store:
    global _store
    if _store is None:
        _store = _Store()
    return _store


class CheckIn(BaseModel):
    claim_id: str
    claim_text: str
    overall: str


class BoothIn(BaseModel):
    booth_id: str


async def _do(coro):
    try:
        return await coro
    except httpx.HTTPError:
        raise HTTPException(502, "account store unavailable")


@router.get("/me/checks")
async def me_checks(authorization: str | None = Header(None)):
    return await _do(account().list("wa_saved_checks", _user(authorization)))


@router.post("/me/checks")
async def me_checks_add(body: CheckIn, authorization: str | None = Header(None)):
    await _do(account().put("wa_saved_checks", _user(authorization), "claim_id", body.model_dump()))
    return {"ok": True}


@router.delete("/me/checks/{claim_id}")
async def me_checks_del(claim_id: str, authorization: str | None = Header(None)):
    await _do(account().delete("wa_saved_checks", _user(authorization), "claim_id", claim_id))
    return {"ok": True}


@router.get("/me/booths")
async def me_booths(authorization: str | None = Header(None)):
    return await _do(account().list("wa_watched_booths", _user(authorization)))


@router.post("/me/booths")
async def me_booths_add(body: BoothIn, authorization: str | None = Header(None)):
    await _do(account().put("wa_watched_booths", _user(authorization), "booth_id", body.model_dump()))
    return {"ok": True}


@router.delete("/me/booths/{booth_id}")
async def me_booths_del(booth_id: str, authorization: str | None = Header(None)):
    await _do(account().delete("wa_watched_booths", _user(authorization), "booth_id", booth_id))
    return {"ok": True}


# ------------------------------------------------------------------ worker endpoints
@router.get("/wa/outbox")
async def wa_outbox(wait: float = 20, x_wa_secret: str | None = Header(None)):
    _check_worker(x_wa_secret)
    _beat()
    if not _outbox:
        _evt().clear()
        try:
            await asyncio.wait_for(_evt().wait(), timeout=max(0.0, min(wait, 30.0)))
        except asyncio.TimeoutError:
            pass
        _beat()
    msgs, _outbox[:] = list(_outbox), []
    return {"messages": msgs}


class Heartbeat(BaseModel):
    state: str
    number: str | None = None


@router.post("/wa/heartbeat")
async def wa_heartbeat(hb: Heartbeat, x_wa_secret: str | None = Header(None)):
    _check_worker(x_wa_secret)
    _beat(hb.state, mask(n) if (n := normalize(hb.number or "")) else None)
    return {"ok": True}


class Inbound(BaseModel):
    model_config = {"populate_by_name": True}
    sender: str = Field("", alias="from")
    text: str = ""
    image_b64: str | None = None
    audio_b64: str | None = None  # a WhatsApp voice note (OGG/Opus)
    unsupported: bool = False  # a sticker, document, video, location or contact


@router.post("/wa/inbound")
async def wa_inbound(msg: Inbound, x_wa_secret: str | None = Header(None)):
    """Same logic as the Telegram bot (bot/core.py), calling this app in-process."""
    _check_worker(x_wa_secret)
    _beat()
    from api.main import app  # late import: api.main includes this router
    from bot import core
    from bot.texts import L, with_footer
    image = None
    if msg.image_b64:
        try:
            image = base64.b64decode(msg.image_b64)
        except ValueError:
            image = None
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://rollwatch",
                                 timeout=core.TIMEOUT) as client:
        api = core.Api(base="http://rollwatch", client=client, channel="whatsapp")
        text = (msg.text or "").strip()
        audio = None
        if msg.audio_b64:
            try:
                audio = base64.b64decode(msg.audio_b64)
            except ValueError:
                audio = None
        if msg.unsupported and not (text or audio or image is not None):
            replies = [core.Reply("text", with_footer(L["unsupported"]["hi"] + "\n\n" + L["unsupported"]["en"], "hi"))]
        elif audio:
            replies = await core.handle_voice(api, audio)
        elif image is not None:
            replies = await core.handle_claim(api, text=core.strip_claim_prefix(text) or None, image=image)
        elif text:
            replies = await core.handle_text(api, text)
        else:
            lang = "en"
            replies = [core.Reply("text", with_footer(L["start"][lang], lang))]
    out: list[dict] = []
    for r in replies:
        if r.kind == "text":
            out.append({"text": r.text})
        elif r.kind == "photo" and r.data:
            out.append({"text": "", "image_b64": base64.b64encode(r.data).decode("ascii")})
        elif r.kind in ("voice", "audio") and r.data:
            out.append({"text": "", "audio_b64": base64.b64encode(r.data).decode("ascii"),
                        "audio_mime": "audio/ogg; codecs=opus" if r.kind == "voice" else "audio/mpeg",
                        "ptt": r.kind == "voice"})
    return {"replies": out}


@router.get("/wa/status")
async def wa_status():
    seen = _worker["seen"]
    return {"state": _worker["state"] if _worker_online() else "offline",
            "last_seen_s": int(time.time() - seen) if seen else None,
            "number": _worker["number"], "store": account().kind}
