"""Request log -> artifacts/ops.jsonl and the /ops summary (TRD 1.1, M11)."""
from __future__ import annotations

import contextvars
import json
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
    try:
        return await call_next(request)
    finally:
        rec["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        _req.reset(tok)
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
    return {
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
