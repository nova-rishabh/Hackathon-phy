"""RollWatch Centralized Uptime & Error Monitoring Subsystem.

Tracks and monitors the 5 core tiers:
1. Web: Next.js frontend availability & synthetic probe
2. API: FastAPI core uptime, request rate, 5xx errors, latency
3. Redis: Shared storage connectivity, ping round-trip, fallback state
4. Telegram: Bot worker polling heartbeat & exception tracking
5. WhatsApp: Baileys bridge worker connection state, qr/pairing, outbox & inbound errors
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

_START_TIME = time.time()
_LOCK = threading.Lock()

# Sliding windows
_RECENT_ERRORS: deque[dict[str, Any]] = deque(maxlen=100)
_REQUEST_HISTORY: deque[tuple[float, int, float]] = deque(maxlen=1000)  # (timestamp, status_code, latency_ms)

_HEARTBEATS: dict[str, dict[str, Any]] = {
    "web": {"last_seen": 0.0, "state": "unknown", "details": {}},
    "api": {"last_seen": time.time(), "state": "healthy", "details": {"version": "1.0"}},
    "redis": {"last_seen": 0.0, "state": "unknown", "details": {}},
    "telegram": {"last_seen": 0.0, "state": "unknown", "details": {}},
    "whatsapp": {"last_seen": 0.0, "state": "unknown", "details": {}},
}

_ERROR_COUNTERS: dict[str, int] = {
    "web": 0,
    "api": 0,
    "redis": 0,
    "telegram": 0,
    "whatsapp": 0,
}


def _iso(ts: float) -> str:
    if not ts:
        return "never"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def record_request(status_code: int, latency_ms: float):
    now = time.time()
    with _LOCK:
        _REQUEST_HISTORY.append((now, status_code, latency_ms))
        if status_code >= 500:
            _ERROR_COUNTERS["api"] += 1
            _RECENT_ERRORS.append({
                "timestamp": _iso(now),
                "component": "api",
                "level": "error",
                "message": f"HTTP {status_code}",
                "latency_ms": round(latency_ms, 2),
            })


def record_error(component: str, message: str, level: str = "error", details: dict[str, Any] | None = None):
    now = time.time()
    comp = component.lower()
    with _LOCK:
        if comp in _ERROR_COUNTERS:
            _ERROR_COUNTERS[comp] += 1
        else:
            _ERROR_COUNTERS[comp] = 1
        _RECENT_ERRORS.append({
            "timestamp": _iso(now),
            "component": comp,
            "level": level,
            "message": str(message)[:500],
            "details": details or {},
        })


def record_heartbeat(component: str, state: str = "healthy", details: dict[str, Any] | None = None):
    now = time.time()
    comp = component.lower()
    with _LOCK:
        _HEARTBEATS[comp] = {
            "last_seen": now,
            "state": state,
            "details": details or {},
        }


async def _probe_web(timeout: float = 3.0) -> dict[str, Any]:
    """Check Next.js frontend accessibility."""
    web_base = os.environ.get("WEB_BASE") or os.environ.get("NEXT_PUBLIC_APP_URL") or "http://localhost:3000"
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(web_base)
            latency = round((time.perf_counter() - t0) * 1000, 2)
            is_ok = resp.status_code in (200, 304, 307, 308)
            record_heartbeat("web", "healthy" if is_ok else "degraded", {
                "url": web_base,
                "status_code": resp.status_code,
                "latency_ms": latency,
            })
            return {
                "status": "healthy" if is_ok else "degraded",
                "latency_ms": latency,
                "http_status": resp.status_code,
                "url": web_base,
            }
    except Exception as e:
        record_heartbeat("web", "offline", {"url": web_base, "error": str(e)})
        return {
            "status": "offline",
            "latency_ms": None,
            "http_status": None,
            "error": str(e),
            "url": web_base,
        }


async def _probe_redis(timeout: float = 2.0) -> dict[str, Any]:
    """Check Redis connectivity and round-trip ping."""
    from api import shared
    s = shared.state()
    kind = getattr(s, "kind", "unknown")
    if "redis" not in kind:
        return {
            "status": "healthy" if "memory" in kind else "degraded",
            "mode": kind,
            "latency_ms": 0.05,
            "note": "In-memory failover active (single-process mode)",
        }

    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        return {
            "status": "healthy",
            "mode": "memory",
            "latency_ms": 0.05,
            "note": "REDIS_URL not configured; running in memory",
        }

    t0 = time.perf_counter()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, socket_connect_timeout=timeout, socket_timeout=timeout)
        await r.ping()
        await r.aclose()
        latency = round((time.perf_counter() - t0) * 1000, 2)
        record_heartbeat("redis", "healthy", {"latency_ms": latency})
        return {
            "status": "healthy",
            "mode": "redis",
            "latency_ms": latency,
        }
    except Exception as e:
        record_error("redis", f"Redis ping failure: {e}")
        record_heartbeat("redis", "degraded", {"error": str(e)})
        return {
            "status": "degraded",
            "mode": "redis_failed_over_to_memory",
            "latency_ms": None,
            "error": str(e),
        }


async def _get_whatsapp_status() -> dict[str, Any]:
    from api import shared
    s = shared.state()
    try:
        w = await s.worker()
        last_seen = float(w.get("seen", 0) or 0)
        age = time.time() - last_seen if last_seen > 0 else 999999
        raw_state = w.get("state", "offline")
        if age < 45 and raw_state == "connected":
            status = "healthy"
        elif age < 60 and raw_state in ("qr", "connecting"):
            status = "degraded"
        else:
            status = "offline" if last_seen == 0 else "degraded"
        return {
            "status": status,
            "worker_state": raw_state,
            "last_heartbeat_seconds_ago": round(age, 1) if last_seen > 0 else None,
            "last_seen": _iso(last_seen) if last_seen > 0 else "never",
            "number": w.get("number"),
        }
    except Exception as e:
        return {"status": "offline", "error": str(e)}


def _get_telegram_status() -> dict[str, Any]:
    hb = _HEARTBEATS.get("telegram", {})
    last_seen = hb.get("last_seen", 0.0)
    age = time.time() - last_seen if last_seen > 0 else 999999
    if last_seen > 0 and age < 60:
        status = "healthy"
    elif last_seen > 0 and age < 180:
        status = "degraded"
    else:
        status = "offline"
    return {
        "status": status,
        "last_seen": _iso(last_seen),
        "last_heartbeat_seconds_ago": round(age, 1) if last_seen > 0 else None,
        "details": hb.get("details", {}),
    }


def _get_api_metrics() -> dict[str, Any]:
    now = time.time()
    with _LOCK:
        recent = [req for req in _REQUEST_HISTORY if now - req[0] <= 300]
        one_min = [req for req in _REQUEST_HISTORY if now - req[0] <= 60]

    latencies = [req[2] for req in recent]
    lat_p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0.0
    lat_p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0

    errors_5m = sum(1 for req in recent if req[1] >= 500)
    errors_1m = sum(1 for req in one_min if req[1] >= 500)

    error_rate_5m = (errors_5m / len(recent) * 100) if recent else 0.0

    status = "healthy"
    if error_rate_5m > 5.0 or lat_p95 > 3000:
        status = "degraded"
    if error_rate_5m > 25.0:
        status = "critical"

    return {
        "status": status,
        "uptime_seconds": round(now - _START_TIME, 1),
        "requests_total": len(_REQUEST_HISTORY),
        "requests_last_5m": len(recent),
        "errors_last_5m": errors_5m,
        "errors_last_1m": errors_1m,
        "error_rate_pct": round(error_rate_5m, 2),
        "latency_p50_ms": round(lat_p50, 1),
        "latency_p95_ms": round(lat_p95, 1),
    }


async def get_system_monitoring(probe_remote_web: bool = False) -> dict[str, Any]:
    api_metrics = _get_api_metrics()
    redis_metrics = await _probe_redis()
    tg_metrics = _get_telegram_status()
    wa_metrics = await _get_whatsapp_status()

    web_metrics: dict[str, Any]
    if probe_remote_web:
        web_metrics = await _probe_web()
    else:
        hb = _HEARTBEATS.get("web", {})
        web_metrics = {
            "status": hb.get("state", "healthy"),
            "last_seen": _iso(hb.get("last_seen", 0.0)),
            "details": hb.get("details", {}),
        }

    # Aggregate overall status
    statuses = [api_metrics["status"], redis_metrics["status"], web_metrics["status"]]
    if "critical" in statuses or api_metrics["status"] == "critical":
        overall = "critical"
    elif "degraded" in statuses or "offline" in [tg_metrics["status"], wa_metrics["status"]]:
        overall = "degraded"
    else:
        overall = "healthy"

    with _LOCK:
        errors_copy = list(_RECENT_ERRORS)

    return {
        "overall_status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "components": {
            "api": api_metrics,
            "web": web_metrics,
            "redis": redis_metrics,
            "telegram": tg_metrics,
            "whatsapp": wa_metrics,
        },
        "error_counters": dict(_ERROR_COUNTERS),
        "recent_errors": errors_copy[-20:],
    }


class HeartbeatPayload(BaseModel):
    component: str
    state: str = "healthy"
    details: dict[str, Any] | None = None


class ErrorPayload(BaseModel):
    component: str
    message: str
    level: str = "error"
    details: dict[str, Any] | None = None

