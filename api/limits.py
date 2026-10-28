"""Per-client rate limits and input caps for the public endpoints that cost money (Gemini, ElevenLabs, Razorpay)
or CPU (audit, story recompute). Counts live in api/shared.py, so they hold across workers when REDIS_URL is set.

Limits are generous on purpose: many people on one venue Wi-Fi share an IP.
"""
from __future__ import annotations

import hmac
import os
import time

from fastapi import HTTPException, Request

from api import shared

# bucket -> (requests, window seconds)
LIMITS = {
    "voice": (20, 60),       # ElevenLabs
    "claims": (30, 60),      # Gemini split (cached answers are free, but new claims are not)
    "ask": (60, 60),
    "stories": (60, 60),
    "audit": (4, 60),        # a full engine run per request
    "cards": (60, 60),       # may trigger a render on the web app
    "subscribe": (6, 600),   # creates objects in the Razorpay account
    "orgs": (5, 3600),       # new workspaces
    "incremental": (10, 60), # partial engine runs
}
MAX_TEXT = 4000                  # characters of claim or question text
MAX_B64 = 8_000_000              # ~6 MB image or audio, base64
MAX_AUDIT = 40_000_000           # characters of CSV across both rolls and context files


def client_ip(request: Request) -> str:
    """The address the hosting proxy saw. Render appends the real client last in X-Forwarded-For; earlier entries
    are whatever the caller sent, so they can't be trusted for limits."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[-1].strip()
    return request.client.host if request.client else "?"


def trusted(request: Request) -> bool:
    want = os.environ.get("WA_WORKER_SECRET", "")
    got = request.headers.get("x-wa-secret", "")
    return bool(want and got) and hmac.compare_digest(got.encode("utf-8"), want.encode("utf-8"))


def rate(bucket: str):
    """FastAPI dependency: 429 with Retry-After once a client exceeds the bucket's limit."""
    n, window = LIMITS[bucket]

    async def dep(request: Request):
        if trusted(request):  # the WhatsApp bridge and Telegram bot carry many users; they limit per user instead
            return
        key, now = f"{bucket}:{client_ip(request)}", time.time()
        wait = await shared.state().wait_for(key, n, window, now)
        if wait:
            raise HTTPException(429, f"too many requests; try again in {wait} s", headers={"Retry-After": str(wait)})
        await shared.state().hit(key, now, window)
    return dep


def cap(value: str | None, limit: int, what: str):
    if value and len(value) > limit:
        raise HTTPException(413, f"{what} is too large")
