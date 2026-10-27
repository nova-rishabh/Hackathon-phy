"""WhatsApp sign-in (6-digit code), account data and the WhatsApp worker bridge.

The WhatsApp Web session runs in wa/worker.js on a laptop that only makes OUTBOUND calls here:
it long-polls /wa/outbox, heartbeats, and forwards inbound chats to /wa/inbound. This API owns the
codes, tokens and account rows. Codes are stored only as sha256(mobile+code+AUTH_SECRET).
Never logged: codes, tokens, full phone numbers, secrets (ops.jsonl records the route path only).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api import constants as C, shared

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


# ------------------------------------------------------------------ shared state (memory, or Redis with REDIS_URL)
WA_MSGS, WA_WINDOW = 20, 600  # messages per number per 10 minutes


def S():
    return shared.state()


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


# ------------------------------------------------------------------ worker state + outbox
async def _worker_online() -> bool:
    return time.time() - (await S().worker())["seen"] < HEARTBEAT_TTL


async def _beat(state: str | None = None, number: str | None = None):
    await S().beat(state, number)


def _check_worker(secret: str | None):
    want = os.environ.get("WA_WORKER_SECRET")
    if not want:
        raise HTTPException(503, "WA_WORKER_SECRET is not set: worker endpoints are disabled")
    if not secret or not hmac.compare_digest(secret.encode("utf-8"), want.encode("utf-8")):
        raise HTTPException(403, "bad worker secret")


# ------------------------------------------------------------------ codes + tokens


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
    wait = max([await S().wait_for(k, n, w, now) for k, n, w in keys])
    if wait:
        return _err(429, error="rate_limited", retry_in=wait)
    if not await _worker_online():
        return _err(503, error="sender_offline")
    for k, _, w in keys:
        await S().hit(k, now, w)
    code = f"{secrets.randbelow(10 ** 6):06d}"
    await S().otp_set(m, {"h": _code_hash(m, code), "exp": now + CODE_TTL, "left": MAX_ATTEMPTS}, CODE_TTL)
    await S().put({"id": secrets.token_hex(8), "to": m, "text": C.WA_OTP_TEXT["en"].format(code=code)})
    return {"sent": True, "to": mask(m), "expires_in": CODE_TTL}


@router.post("/auth/wa/verify")
async def wa_verify(req: VerifyReq):
    m = normalize(req.mobile)
    p = await S().otp_get(m) if m else None
    if not p:
        return _err(410, error="expired")
    if time.time() > p["exp"] or p["left"] <= 0:
        await S().otp_del(m)
        return _err(410, error="expired")
    code = re.sub(r"\D", "", req.code or "")
    if not hmac.compare_digest(_code_hash(m, code), p["h"]):
        p["left"] -= 1
        if p["left"] <= 0:
            await S().otp_del(m)
        else:
            await S().otp_set(m, p, max(1, int(p["exp"] - time.time())))
        return _err(401, error="wrong_code", attempts_left=max(p["left"], 0))
    await S().otp_del(m)
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

    async def all(self, table: str) -> list[dict]:
        """Every row with its phone (server-side alerts only; never exposed through an endpoint)."""
        if self.kind == "memory":
            return [{**r, "phone": p} for p, rows in self.mem.items() for (t, _), r in rows.items() if t == table]
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{self.url}/rest/v1/{table}", headers=self._h(), params={"select": "*"})
        r.raise_for_status()
        return r.json()

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


def booth_status(booth_id: str) -> str | None:
    """One line on a booth, every number from the engine; wording from constants."""
    from api.store import store
    s = store()
    st = s.stories.get(booth_id)
    if st is None:
        return None
    un = next((x for x in st.stories if x.code == "unexplained"), None)
    spike = next((f for f in s.flags if f.type == "deletion_spike" and f.scope.booth_id == booth_id), None)
    label = C.WA_BOOTH_LABEL["normal" if spike is None else "benign" if spike.likely_benign else "review"]
    tpl = C.WA_BOOTH_STATUS["en_normal" if spike is None else "en"]
    return tpl.format(b=int(booth_id[1:]), removed=st.removed_total,
                                          unexplained=round((un.share if un else 0) * 100), label=label)


async def _queue(to: str, text: str):
    await S().put({"id": secrets.token_hex(8), "to": to, "text": text})


@router.post("/me/booths")
async def me_booths_add(body: BoothIn, authorization: str | None = Header(None)):
    phone = _user(authorization)
    await _do(account().put("wa_watched_booths", phone, "booth_id", body.model_dump()))
    status = booth_status(body.booth_id)
    if status and await _worker_online():  # confirm on WhatsApp with the booth's state right now
        await _queue(phone, C.WA_WATCH_TEXT["en"].format(b=int(body.booth_id[1:]), status=status))
    return {"ok": True}


@router.post("/wa/alerts")
async def wa_alerts(x_wa_secret: str | None = Header(None)):
    """After a new audit run: every watcher gets their booth's latest state. Worker secret only."""
    _check_worker(x_wa_secret)
    web = os.environ.get("WEB_BASE", "https://rollwatch-web.onrender.com").rstrip("/")
    rows = await _do(account().all("wa_watched_booths"))
    sent = 0
    for r in rows:
        status = booth_status(r["booth_id"])
        if status:
            await _queue(r["phone"], C.WA_ALERT_TEXT["en"].format(status=status, link=f"{web}/"))
            sent += 1
    return {"queued": sent}


@router.delete("/me/booths/{booth_id}")
async def me_booths_del(booth_id: str, authorization: str | None = Header(None)):
    await _do(account().delete("wa_watched_booths", _user(authorization), "booth_id", booth_id))
    return {"ok": True}


# ------------------------------------------------------------------ worker endpoints
@router.get("/wa/outbox")
async def wa_outbox(wait: float = 20, x_wa_secret: str | None = Header(None)):
    _check_worker(x_wa_secret)
    await _beat()
    msgs = await S().take(max(0.0, min(wait, 30.0)))
    await _beat()
    return {"messages": msgs}


class Heartbeat(BaseModel):
    state: str
    number: str | None = None


@router.post("/wa/heartbeat")
async def wa_heartbeat(hb: Heartbeat, x_wa_secret: str | None = Header(None)):
    _check_worker(x_wa_secret)
    masked_no = mask(n) if (n := normalize(hb.number or "")) else None
    await _beat(hb.state, masked_no)
    try:
        from api import monitoring
        monitoring.record_heartbeat("whatsapp", hb.state, {"number": masked_no})
    except Exception:
        pass
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
    await _beat()
    if msg.sender:  # per-number limit; say "slow down" once per window, then stay quiet
        now, key = time.time(), f"wa:{msg.sender}"
        if await S().wait_for(key, WA_MSGS, WA_WINDOW, now):
            if not await S().wait_for(key + ":told", 1, WA_WINDOW, now):
                await S().hit(key + ":told", now, WA_WINDOW)
                return {"replies": [{"text": C.WA_SLOW_TEXT["en"]}]}
            return {"replies": []}
        await S().hit(key, now, WA_WINDOW)
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
    w = await S().worker()
    seen = w["seen"]
    return {"state": w["state"] if time.time() - seen < HEARTBEAT_TTL else "offline",
            "last_seen_s": int(time.time() - seen) if seen else None,
            "number": w["number"], "store": account().kind, "shared_state": S().kind}
