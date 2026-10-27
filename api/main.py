"""RollWatch API: one FastAPI process on :8000 (TRD §1, §3.5; contracts/api.md).

Serves the frozen artifacts from memory. DEMO_MODE=1 reads only artifacts/ and cache/llm/;
every LLM path falls back to its template when there is no key or no cache entry.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import tempfile
import threading
import time
from pathlib import Path

import os

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")  # keys stay out of git (.gitignore); real env vars win
if os.environ.get("DEMO_MODE", "0") == "1":
    # Demo mode: data only from artifacts/, LLM only from cache/llm/ (cache miss -> template). No overrides.
    os.environ["ROLLWATCH_DATA"] = str(_ROOT / "artifacts")
    os.environ["ROLLWATCH_CACHE"] = str(_ROOT / "cache" / "llm")
    os.environ.pop("ROLLWATCH_OPS", None)

from fastapi import Depends, FastAPI, Header, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from api import billing, citizen, limits, claims, guard as guard_mod, jobs, keys, llm, monitoring, ops, voice, wa_auth
from api.store import ROOT, data_dir, store
from contracts.models import (AuditEntry, ClaimCheckRequest, ClaimVerdict, EngineRunResult, Flag, FlagList,
                              GuardLog, Health, Overview, Review, ReviewRequest, ReviewResponse, RuleCard,
                              StoryResult, StoryToggleRequest)

app = FastAPI(title="RollWatch API", version="1.0")
app.middleware("http")(ops.middleware)  # logs route + timings only, never headers
app.middleware("http")(keys.middleware)  # BYOK: X-Gemini-Key / X-ElevenLabs-Key -> contextvar (never stored)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*", "Authorization", "Content-Type", "X-Gemini-Key", "X-ElevenLabs-Key"])
app.include_router(citizen.router)  # GET /search, POST /citizen/ask (owned by B2)
app.include_router(voice.router)  # POST /voice/tts, POST /voice/stt (ElevenLabs)
app.include_router(wa_auth.router)  # WhatsApp sign-in code, /me account data, /wa/* worker bridge
app.include_router(billing.router)  # pricing quotes and Razorpay custom subscriptions
app.include_router(jobs.router)  # asynchronous constituency-level audit jobs

_lock = threading.Lock()
_claims: dict[str, ClaimVerdict] = {}


def demo_mode() -> bool:
    return llm.demo_mode()


@app.on_event("startup")
def _warm():
    store()  # load artifacts + aggregates once
    try:
        citizen.store()
    except Exception:
        pass


# ------------------------------------------------------------------ core
@app.get("/health", response_model=Health)
def health():
    d = data_dir()
    roll = d / "roll_v2.parquet"
    roll_v = hashlib.sha256(f"{roll.stat().st_size}:{int(roll.stat().st_mtime)}".encode()).hexdigest()[:8] if roll.exists() else "none"
    return Health(ok=True, demo_mode=demo_mode(),
                  versions={"roll": roll_v, "engine": str(len(store().flags)) + " flags",
                            "cache": str(llm.cache_count())})


@app.get("/health/ready")
def health_ready():
    """Readiness probe: checks whether data files and flags are loaded."""
    try:
        s = store()
        has_flags = len(s.flags) > 0
        return {"ready": True, "flags_count": len(s.flags), "booths_count": len(s.overview().booths)}
    except Exception as e:
        raise HTTPException(503, f"Service not ready: {e}")


@app.get("/health/live")
def health_live():
    """Liveness probe: verifies process is alive and responsive."""
    return {"live": True, "timestamp": time.time()}


@app.get("/keys/status")
def keys_status():
    """Which key each feature would use for this request: "byok" (header), "server" (env) or "none"."""
    return keys.status()


# Answers that only change when the engine reruns: serialized once, then served as bytes with cache headers,
# so a browser or CDN in front can answer most traffic without reaching Python at all.
_FROZEN: dict[str, bytes] = {}


def _frozen(key: str, build) -> Response:
    if key not in _FROZEN:
        obj = build()
        _FROZEN[key] = (obj.model_dump_json() if hasattr(obj, "model_dump_json")
                        else json.dumps([o.model_dump(mode="json") for o in obj], ensure_ascii=False)).encode("utf-8")
    return Response(_FROZEN[key], media_type="application/json", headers={"Cache-Control": "public, max-age=300"})


def _frozen_dict(key: str, build) -> Response:
    if key not in _FROZEN:
        _FROZEN[key] = json.dumps(build(), ensure_ascii=False).encode("utf-8")
    return Response(_FROZEN[key], media_type="application/json", headers={"Cache-Control": "public, max-age=300"})


@app.get("/overview", response_model=Overview)
def overview():
    return _frozen("overview", lambda: store().overview())


def _with_stories(f: Flag) -> Flag:
    if f.type == "deletion_spike" and f.stories is None:
        st = store().stories.get(f.scope.booth_id)
        if st:
            return f.model_copy(update={"stories": st})
    return f


@app.get("/flags", response_model=FlagList)
def flags(type: str | None = None, booth_id: str | None = None, band: str | None = None,
          likely_benign: bool | None = None, status: str | None = None,
          limit: int | None = Query(None, ge=1), offset: int = Query(0, ge=0)):
    items = store().flags
    if type:
        items = [f for f in items if f.type == type]
    if booth_id:
        items = [f for f in items if f.scope.booth_id == booth_id]
    if band:
        items = [f for f in items if f.confidence_band == band]
    if likely_benign is not None:
        items = [f for f in items if f.likely_benign == likely_benign]
    if status:
        items = [f for f in items if f.review.status == status]
    items = sorted(items, key=lambda f: -f.confidence)
    page = items[offset: offset + limit] if limit else items[offset:]
    return FlagList(items=[_with_stories(f) for f in page], total=len(items))


@app.get("/flags/{flag_id}", response_model=Flag)
def flag(flag_id: str):
    f = store().flag_by_id.get(flag_id)
    if not f:
        raise HTTPException(404, "unknown flag_id")
    return _with_stories(f)


@app.post("/stories/{booth_id}", response_model=StoryResult)
def stories(booth_id: str, req: StoryToggleRequest, _=Depends(limits.rate("stories"))):
    s = store()
    if booth_id not in s.agg:
        raise HTTPException(404, "unknown booth_id")
    res = s.toggle(booth_id, list(req.context_on))
    if res is None:
        raise HTTPException(404, "no removals in this booth")
    return res


# ------------------------------------------------------------------ engine
_cal = None


def _calibrator():
    global _cal
    from engine.confidence import Calibrator
    from engine.run import train_calibrator
    if _cal is None:
        tr = data_dir() / "training"
        key = tr / "answer_key.json"
        _cal = train_calibrator(str(tr), str(key)) if key.exists() else Calibrator()
    return _cal


def _run_engine(d: str) -> dict:
    from engine.run import analyse, build_flags, raw_flags
    t0 = time.time()
    an = analyse(d)
    fl = build_flags(raw_flags(an), _calibrator())
    by: dict[str, int] = {}
    for f in fl:
        by[f.type] = by.get(f.type, 0) + 1
    return {"flags": fl, "stories": an["stories"], "by_type": by, "runtime_ms": int((time.time() - t0) * 1000)}


@app.post("/engine/run", response_model=EngineRunResult)
def engine_run(x_wa_secret: str | None = Header(None)):
    wa_auth._check_worker(x_wa_secret)  # a full engine rerun: operators only, never the public
    """Re-runs the engine on the frozen roll (in memory; artifacts are not overwritten)."""
    with _lock:
        r = _run_engine(str(data_dir()))
    return EngineRunResult(flags_total=len(r["flags"]), by_type=r["by_type"], runtime_ms=r["runtime_ms"])


class AuditRequest(BaseModel):
    """M12 integration input: two rolls in the open RollRow schema, as CSV text or base64 parquet."""
    roll_v1_csv: str | None = None
    roll_v2_csv: str | None = None
    roll_v1_parquet_b64: str | None = None
    roll_v2_parquet_b64: str | None = None
    death_register_csv: str | None = None
    hostel_list_csv: str | None = None
    boundary_changes_csv: str | None = None
    include_relation_conflicts: bool = False


@app.post("/audit")
def audit(req: AuditRequest, _=Depends(limits.rate("audit"))):
    total = sum(len(getattr(req, f) or "") for f in ("roll_v1_csv", "roll_v2_csv", "roll_v1_parquet_b64", "roll_v2_parquet_b64",
                                                     "death_register_csv", "hostel_list_csv", "boundary_changes_csv"))
    if total > limits.MAX_AUDIT:
        raise HTTPException(413, "the rolls are too large for this demo server; run the open engine on your own machine")
    """Pre-publication check (PRD M12): run the open engine on a draft roll and return flags + stories."""
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        for v in ("v1", "v2"):
            csv, pq = getattr(req, f"roll_{v}_csv"), getattr(req, f"roll_{v}_parquet_b64")
            if pq:
                (t / f"roll_{v}.parquet").write_bytes(base64.b64decode(pq))
            elif csv:
                (t / f"roll_{v}.csv").write_text(csv, encoding="utf-8")
            else:
                raise HTTPException(422, f"roll_{v} missing (send roll_{v}_csv or roll_{v}_parquet_b64)")
        for name in ("death_register", "hostel_list", "boundary_changes"):
            txt = getattr(req, f"{name}_csv")
            if txt:
                (t / f"{name}.csv").write_text(txt, encoding="utf-8")
        try:
            r = _run_engine(td)
        except (KeyError, ValueError) as e:
            raise HTTPException(422, f"input does not match the RollRow schema: {e}")
    fl = [f for f in r["flags"] if req.include_relation_conflicts or f.type != "relation_conflict"]
    fl.sort(key=lambda f: -f.confidence)
    return {"flags": [f.model_dump(mode="json") for f in fl],
            "stories": [s.model_dump(mode="json") for s in r["stories"].values()],
            "by_type": r["by_type"], "flags_total": len(r["flags"]), "runtime_ms": r["runtime_ms"],
            "needs_human_review": True}


@app.get("/eval")
def eval_():
    if store().eval_result() is None:
        raise HTTPException(404, "the blind eval has not run yet")
    return _frozen("eval", lambda: store().eval_result())


@app.get("/eval/blind")
def eval_blind():
    """The blind test: a separate agent planted anomalies and decoys in a fresh district and kept the key; the
    engine (calibrated only on public training districts) never saw it. Published scoreboard only."""
    def build():
        d = ROOT / "api" / "data"
        e = json.loads((d / "blind_eval.json").read_text(encoding="utf-8"))
        r = json.loads((d / "blind_rules.json").read_text(encoding="utf-8"))
        rules = [{"rule": x["rule"], "raised": x["flags_raised"], "false_positive_rate": x["false_positive_rate"]}
                 for x in r["rules"] if not x["rule"].startswith("official_")]
        return {"eval": e, "rules": rules, "planted_by": "a separate AI agent; config and key kept private",
                "calibration": "four public training districts only"}
    try:
        return _frozen_dict("eval_blind", build)
    except (OSError, ValueError, KeyError):
        raise HTTPException(404, "the blind test has not been published")


@app.get("/rules", response_model=list[RuleCard])
def rules():
    return _frozen("rules", lambda: store().rule_cards() or [])


# ------------------------------------------------------------------ claims
def _claims_dir() -> Path:
    return data_dir() / "claims"


@app.post("/claims/check", response_model=ClaimVerdict)
def claims_check(req: ClaimCheckRequest, _=Depends(limits.rate("claims"))):
    limits.cap(req.text, limits.MAX_TEXT, "the claim text")
    limits.cap(req.image_b64, limits.MAX_B64, "the screenshot")
    if not (req.text or req.image_b64):
        raise HTTPException(422, "send text or image_b64")
    v = claims.check(req)
    v.card_png = f"/cards/{v.claim_id}.png"  # drawn on first request by the web app and cached (card_png route)
    _claims[v.claim_id] = v
    try:
        _claims_dir().mkdir(parents=True, exist_ok=True)
        (_claims_dir() / f"{v.claim_id}.json").write_text(v.model_dump_json(), encoding="utf-8")
    except OSError:
        pass
    return v


@app.get("/claims/{claim_id}", response_model=ClaimVerdict)
def claim_get(claim_id: str):
    v = _claims.get(claim_id)
    if v is None:
        p = _claims_dir() / f"{Path(claim_id).name}.json"
        if not p.exists():
            raise HTTPException(404, "unknown claim_id")
        v = ClaimVerdict.model_validate_json(p.read_text(encoding="utf-8"))
    return v


PNG_MAGIC = bytes([0x89]) + b"PNG"

@app.get("/cards/{claim_id}.png")
def card_png(claim_id: str, _=Depends(limits.rate("cards"))):
    if not re.fullmatch(r"[0-9a-f]{12}", claim_id):  # claim ids are 12 hex characters; nothing else is fetched or written
        raise HTTPException(404, "unknown claim")
    name = f"{claim_id}.png"
    p = next((x for x in (data_dir() / "cards" / name, ROOT / "cards" / name) if x.exists()), None)
    if p is None:  # draw it once on the web app (next/og route) and keep it
        import httpx
        web = os.environ.get("WEB_BASE", "https://rollwatch-web.onrender.com").rstrip("/")
        try:
            r = httpx.get(f"{web}/card/{Path(claim_id).name}/png", timeout=60, follow_redirects=True)
        except httpx.HTTPError:
            r = None
        if r is None or r.status_code != 200 or not r.content.startswith(PNG_MAGIC):
            raise HTTPException(404, "card not rendered")
        p = data_dir() / "cards" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(r.content)
    return FileResponse(p, media_type="image/png")


# ------------------------------------------------------------------ review + audit log (hash chain)
def _audit_path() -> Path:
    return data_dir() / "audit_log.jsonl"


def _audit_entries() -> list[AuditEntry]:
    p = _audit_path()
    if not p.exists():
        return []
    return [AuditEntry.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


@app.post("/review/{flag_id}", response_model=ReviewResponse)
def review(flag_id: str, req: ReviewRequest, authorization: str | None = Header(None)):
    """Signed-in reviewers only (WhatsApp sign-in token). The reviewer enters the hash chain as a salted hash,
    never as a number."""
    who = hashlib.sha256(("reviewer|" + wa_auth._user(authorization)).encode("utf-8")).hexdigest()[:12]
    s = store()
    f = s.flag_by_id.get(flag_id)
    if not f:
        raise HTTPException(404, "unknown flag_id")
    with _lock:
        prev = (_audit_entries() or [None])[-1]
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        prev_hash = prev.hash if prev else None
        action = f"review:{req.status}"
        note_h = hashlib.sha256(req.note.encode("utf-8")).hexdigest()[:12]
        h = hashlib.sha256(f"{prev_hash}|{ts}|{flag_id}|{action}|{note_h}|{who}".encode("utf-8")).hexdigest()
        e = AuditEntry(ts=ts, flag_id=flag_id, action=action, hash=h, prev_hash=prev_hash)
        with open(_audit_path(), "a", encoding="utf-8") as fh:
            fh.write(e.model_dump_json() + "\n")
        f.review = Review(status=req.status, ts=ts, hash=h)
    return ReviewResponse(review=f.review, audit_hash=h)


@app.get("/audit/log", response_model=list[AuditEntry])
def audit_log():
    return _audit_entries()


# ------------------------------------------------------------------ trust
@app.get("/guard/log", response_model=GuardLog)
def guard_log():
    return guard_mod.log()


@app.get("/ops")
def ops_summary():
    return ops.summary()


@app.get("/ops/monitoring")
async def ops_monitoring():
    return await monitoring.get_system_monitoring(probe_remote_web=False)


@app.get("/ops/monitoring/probe")
async def ops_monitoring_probe():
    return await monitoring.get_system_monitoring(probe_remote_web=True)


@app.post("/ops/monitoring/heartbeat")
def ops_monitoring_heartbeat(hb: monitoring.HeartbeatPayload):
    monitoring.record_heartbeat(hb.component, hb.state, hb.details)
    return {"ok": True, "component": hb.component}


@app.post("/ops/monitoring/error")
def ops_monitoring_error(err: monitoring.ErrorPayload):
    monitoring.record_error(err.component, err.message, err.level, err.details)
    return {"ok": True, "recorded": True}


@app.get("/ops/monitoring/errors")
def ops_monitoring_errors(component: str | None = None):
    with monitoring._LOCK:
        errors = list(monitoring._RECENT_ERRORS)
    if component:
        errors = [e for e in errors if e.get("component") == component.lower()]
    return {"errors": errors, "counters": dict(monitoring._ERROR_COUNTERS)}


@app.get("/report")
def report():
    s = store()
    top = sorted((f for f in s.flags if f.type in ("deletion_spike", "addition_spike")), key=lambda f: -f.confidence)
    e = s.eval_result()
    return {"overview": s.overview().model_dump(mode="json"),
            "top_flags": [_with_stories(f).model_dump(mode="json") for f in top[:10]],
            "eval": e.model_dump(mode="json") if e else None,
            "guard": guard_mod.log().model_dump(mode="json", exclude={"items"}),
            "needs_human_review": True}
