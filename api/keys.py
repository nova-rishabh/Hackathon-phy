"""Bring-your-own-key: per-request API keys from headers, falling back to the server's env.

Headers: X-Gemini-Key, X-ElevenLabs-Key. The middleware puts them in a contextvar for the request
only. Keys are never logged, stored or echoed back (ops.jsonl records route + timings only).
"""
from __future__ import annotations

import contextvars
import os

HEADERS = {"gemini": "x-gemini-key", "elevenlabs": "x-elevenlabs-key"}
ENV = {"gemini": "GEMINI_API_KEY", "elevenlabs": "ELEVENLABS_API_KEY"}

_byok: contextvars.ContextVar[dict | None] = contextvars.ContextVar("rw_byok", default=None)


def get(name: str) -> str | None:
    """Request key first (BYOK), then env. None when neither is set."""
    k = (_byok.get() or {}).get(name)
    return k or os.environ.get(ENV[name]) or None


def source(name: str) -> str:
    if (_byok.get() or {}).get(name):
        return "byok"
    return "server" if os.environ.get(ENV[name]) else "none"


def status() -> dict:
    return {n: source(n) for n in HEADERS}


async def middleware(request, call_next):
    vals = {n: (request.headers.get(h) or "").strip() or None for n, h in HEADERS.items()}
    tok = _byok.set(vals)
    try:
        return await call_next(request)
    finally:
        _byok.reset(tok)
