"""Request log -> artifacts/ops.jsonl and the /ops summary (TRD 1.1, M11)."""
from __future__ import annotations

import contextvars
import json
import math
import os
import threading
import time
from pathlib import Path

import numpy as np

from api import constants as C

ROOT = Path(__file__).resolve().parent.parent
_req: contextvars.ContextVar[dict | None] = contextvars.ContextVar("rw_req", default=None)
_lock = threading.Lock()


def ops_path() -> Path:
    return Path(os.environ.get("ROLLWATCH_OPS", Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts")) / "ops.jsonl"))


def record_llm(model: str, tokens_in: int, tokens_out: int, cache_hit: bool):
    """Called by api.llm for every LLM call (or cache hit) inside a request."""
    r = _req.get()
    if r is None:
        return
    r["llm_tokens_in"] += int(tokens_in)
    r["llm_tokens_out"] += int(tokens_out)
    r["model"] = model
    r["llm_calls"] += 1
    r["cache_hits"] += int(bool(cache_hit))


def _cost_inr(model: str, tin: int, tout: int) -> float:
    p = C.PRICE_INR_PER_MTOK.get(model or "template", C.PRICE_INR_PER_MTOK["template"])
    return (tin * p["in"] + tout * p["out"]) / 1e6


async def middleware(request, call_next):
    route = request.url.path
    rec = {"route": route, "ms": 0.0, "llm_tokens_in": 0, "llm_tokens_out": 0, "model": None,
           "cache_hit": None, "llm_calls": 0, "cache_hits": 0}
    tok = _req.set(rec)
    t0 = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        try:
            from api import monitoring
            monitoring.record_error("api", f"Unhandled error in {route}: {exc}", details={"route": route})
        except Exception:
            pass
        raise
    finally:
        dur_ms = round((time.perf_counter() - t0) * 1000, 2)
        rec["ms"] = dur_ms
        _req.reset(tok)
        try:
            from api import monitoring
            monitoring.record_request(status_code, dur_ms)
        except Exception:
            pass
        if rec["llm_calls"]:
            rec["cache_hit"] = rec["cache_hits"] == rec["llm_calls"]
        if route not in ("/ops", "/favicon.ico"):
            out = {k: rec[k] for k in ("route", "ms", "llm_tokens_in", "llm_tokens_out", "model", "cache_hit")}
            out["ts"] = time.time()
            _buf.append(json.dumps(out, ensure_ascii=False))
            if len(_buf) >= 200 or out["ts"] - _last[0] > 2.0:  # batch the disk write, not one open() per request
                flush()


_buf: list[str] = []
_last = [0.0]


def flush():
    with _lock:
        lines, _buf[:] = list(_buf), []
        _last[0] = time.time()
        if not lines:
            return
        try:
            p = ops_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except OSError:
            pass


def _norm_route(r: str) -> str:
    parts = r.strip("/").split("/")
    if parts and len(parts) > 1 and (parts[0] in ("flags", "stories", "cards", "review")
                                     or (parts[0] == "claims" and parts[1] != "check")):
        return f"/{parts[0]}/{{id}}"
    return r


def _states() -> dict[str, int]:
    """ECI's official state-wise elector totals (Lok Sabha 2024); comment lines start with #."""
    p = ROOT / C.ELECTORS_FILE
    try:
        rows = [ln.split(",") for ln in p.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")][1:]
        return {r[0]: int(r[1]) for r in rows}
    except (OSError, ValueError, IndexError):
        return {}


def _projection(bench: dict | None, loadtest: dict) -> dict | None:
    """All-India numbers computed from what we measured. Audit: per-voter engine cost on one core times the
    electorate, split across independent constituency runs. Requests: checks per second in a revision window,
    against the measured full-citizen-answer rate on four processes."""
    per_us = ((bench or {}).get("scale") or {}).get("per_voter_us_serial")
    if not per_us:
        return None
    states = _states()
    if not states:
        return None
    n = sum(states.values())
    core_h = n * per_us / 1e6 / 3600
    avg = n * C.SCALE_SHARE_CHECKING / (C.SCALE_WINDOW_DAYS * 86400)
    peak = avg * C.SCALE_PEAK_FACTOR
    rps4 = (((loadtest.get("4") or {}).get("routes") or {}).get("citizen answer") or {}).get("rps")
    return {
        "electors": n, "electors_source": C.ELECTORS_SOURCE, "per_voter_us": per_us,
        "audit_core_hours": round(core_h, 1), "audit_minutes_on_64_cores": round(core_h * 60 / 64, 1),
        "assumption": {"share_checking": C.SCALE_SHARE_CHECKING, "window_days": C.SCALE_WINDOW_DAYS,
                       "peak_factor": C.SCALE_PEAK_FACTOR},
        "checks_per_day": round(avg * 86400), "checks_per_s_avg": round(avg, 1), "checks_per_s_peak": round(peak, 1),
        "citizen_answers_per_s_4proc": rps4,
        "machines_at_peak": math.ceil(peak / rps4) if rps4 else None,
        "states": [{"state": s, "electors": e, "core_hours": round(e * per_us / 1e6 / 3600, 2),
                    f"minutes_on_{C.STATE_AUDIT_CORES}_cores": round(e * per_us / 1e6 / 60 / C.STATE_AUDIT_CORES, 1)}
                   for s, e in sorted(states.items(), key=lambda x: -x[1])],
        "state_cores": C.STATE_AUDIT_CORES,
        "note": "Audit assumes constituencies run as independent jobs; the machine count uses the laptop's measured "
                "lower bound and ignores CDN and claim caching, which cut real load further.",
    }


def summary() -> dict:
    flush()
    rows = []
    p = ops_path()
    if p.exists():
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    by: dict[str, list[float]] = {}
    for r in rows:
        by.setdefault(_norm_route(r["route"]), []).append(float(r["ms"]))
    routes = {k: {"n": len(v), "p50_ms": round(float(np.percentile(v, 50)), 1),
                  "p95_ms": round(float(np.percentile(v, 95)), 1)} for k, v in sorted(by.items())}
    claims = [r for r in rows if r["route"] == "/claims/check"]
    costs = [_cost_inr(r.get("model"), r.get("llm_tokens_in", 0), r.get("llm_tokens_out", 0)) for r in claims]
    llm_rows = [r for r in rows if r.get("cache_hit") is not None]
    all_ms = [float(r["ms"]) for r in rows]
    inr = round(float(np.mean(costs)), 4) if costs else 0.0
    bench_p = Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts")) / "bench.json"
    try:
        bench = json.loads(bench_p.read_text(encoding="utf-8")) if bench_p.exists() else None
    except (OSError, json.JSONDecodeError):
        bench = None
    loadtest = {}  # measured on the dev laptop (python -m engine.loadtest), one vs four worker processes
    for w in (1, 4):
        p = ROOT / "cache" / f"loadtest_{w}w.json"
        try:
            if p.exists():
                loadtest[str(w)] = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "loadtest": loadtest or None,
        "projection": _projection(bench, loadtest),
        "requests": len(rows),
        "p50_ms": round(float(np.percentile(all_ms, 50)), 1) if all_ms else None,
        "p95_ms": round(float(np.percentile(all_ms, 95)), 1) if all_ms else None,
        "inr_per_check": inr,
        "bench": bench,
        "routes": routes,
        "claim_checks": len(claims),
        "inr_per_claim_check": inr,
        "cache_hit_rate": round(sum(1 for r in llm_rows if r["cache_hit"]) / len(llm_rows), 3) if llm_rows else None,
        "llm_requests": len(llm_rows),
        "price_note": "Per-token prices are ASSUMPTIONS in api/constants.py (PRICE_INR_PER_MTOK, USD_INR).",
    }
