"""Asynchronous, constituency-level audit job runner and queue.

Allows large, multi-booth constituency rolls to be submitted for auditing asynchronously
without HTTP timeouts, with real-time progress tracking across analysis phases.

Endpoints:
    POST /jobs/audit          -> submits async audit, returns {job_id, status: "queued", check_url}
    GET  /jobs/{job_id}       -> poll job status, stage, percent completion, and duration
    GET  /jobs/{job_id}/result-> returns full flags, stories, and summary once completed
    GET  /jobs                -> lists active and completed audit jobs
    POST /jobs/{job_id}/cancel-> cancels a queued or running job
"""
from __future__ import annotations

import base64
import json
import secrets
import hmac
import hashlib
import logging
import os
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api import limits

log = logging.getLogger("rollwatch.jobs")
router = APIRouter()
ROOT = Path(__file__).resolve().parent.parent

_LOCK = threading.RLock()
_EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="audit_job_")


def _data_dir() -> Path:
    d = Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _jobs_dir() -> Path:
    d = _data_dir() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _iso(ts: float | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


class JobProgress(BaseModel):
    stage: str = "queued"
    percent: int = 0
    message: str = "Job is queued for execution"
    booths_processed: int = 0
    booths_total: int = 0


class JobSummary(BaseModel):
    flags_total: int = 0
    flags_needing_review: int = 0
    stories_total: int = 0
    unusual_booths: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    runtime_ms: int = 0


class AuditJob(BaseModel):
    job_id: str
    constituency_id: str = "AC005"
    status: str = "queued"  # queued, running, completed, failed, cancelled
    progress: JobProgress = Field(default_factory=JobProgress)
    created_at: float
    started_at: float | None = None
    completed_at: float | None = None
    runtime_ms: int | None = None
    summary: JobSummary | None = None
    error: str | None = None


# In-memory registry of jobs
_JOBS: dict[str, AuditJob] = {}
_CANCELLATIONS: set[str] = set()
_JOB_TOKENS: dict[str, str] = {}  # job_id -> sha256 of the private token handed to whoever submitted it


def _authorize(job_id: str, token: str | None, operator_secret: str | None):
    """Only the submitter (holding the job token) or the operator may see or cancel a job. Unknown and
    unauthorised look the same (404), so job ids can't be probed."""
    if operator_secret:
        from api import wa_auth
        wa_auth._check_worker(operator_secret)
        return
    want = _JOB_TOKENS.get(job_id)
    got = hashlib.sha256((token or "").encode("utf-8")).hexdigest()
    if not (want and token and hmac.compare_digest(want, got)):
        raise HTTPException(404, f"Job {job_id} not found")


def _save_job_index():
    try:
        with _LOCK:
            data = {k: v.model_dump() for k, v in _JOBS.items()}
        p = _jobs_dir() / "index.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("Failed to save jobs index: %s", e)


def _load_job_index():
    p = _jobs_dir() / "index.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            with _LOCK:
                for k, v in data.items():
                    _JOBS[k] = AuditJob.model_validate(v)
        except Exception as e:
            log.warning("Failed to load jobs index: %s", e)


_load_job_index()


class AsyncAuditRequest(BaseModel):
    constituency_id: str = "AC005"
    roll_v1_csv: str | None = None
    roll_v2_csv: str | None = None
    roll_v1_parquet_b64: str | None = None
    roll_v2_parquet_b64: str | None = None
    death_register_csv: str | None = None
    hostel_list_csv: str | None = None
    boundary_changes_csv: str | None = None
    include_relation_conflicts: bool = False


def _execute_audit_job(job_id: str, req_data: dict[str, Any]):
    """Background worker function executing the full engine analysis with progress callbacks."""
    t0 = time.time()
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = t0
        job.progress = JobProgress(stage="preparing_data", percent=10, message="Preparing temporary roll workspace")
        _save_job_index()

    temp_dir = tempfile.mkdtemp(prefix=f"rw_audit_{job_id}_")
    t = Path(temp_dir)
    try:
        # Check cancellation
        if job_id in _CANCELLATIONS:
            raise RuntimeError("Job cancelled by user")

        # 1. Write rolls
        for v in ("v1", "v2"):
            csv = req_data.get(f"roll_{v}_csv")
            pq_b64 = req_data.get(f"roll_{v}_parquet_b64")
            if pq_b64:
                (t / f"roll_{v}.parquet").write_bytes(base64.b64decode(pq_b64))
            elif csv:
                (t / f"roll_{v}.csv").write_text(csv, encoding="utf-8")
            else:
                raise ValueError(f"roll_{v} missing (must provide CSV or parquet_b64)")

        for name in ("death_register", "hostel_list", "boundary_changes"):
            txt = req_data.get(f"{name}_csv")
            if txt:
                (t / f"{name}.csv").write_text(txt, encoding="utf-8")

        # Check cancellation
        if job_id in _CANCELLATIONS:
            raise RuntimeError("Job cancelled by user")

        # 2. Update progress: Engine analysis
        with _LOCK:
            job.progress = JobProgress(stage="statistical_tests", percent=35, message="Running booth binomial and Benjamini-Hochberg tests")
            _save_job_index()

        from engine.run import analyse, build_flags, raw_flags
        from api.main import _calibrator

        an = analyse(t)

        if job_id in _CANCELLATIONS:
            raise RuntimeError("Job cancelled by user")

        # 3. Update progress: Stories and flags
        with _LOCK:
            total_b = len(an.get("stories", {}))
            job.progress = JobProgress(
                stage="story_attribution",
                percent=70,
                message="Attributing deletions against context records and duplicate clusters",
                booths_processed=total_b,
                booths_total=total_b,
            )
            _save_job_index()

        fl = build_flags(raw_flags(an), _calibrator())
        if not req_data.get("include_relation_conflicts", False):
            fl = [f for f in fl if f.type != "relation_conflict"]
        fl.sort(key=lambda f: -f.confidence)

        # 4. Result preparation
        by: dict[str, int] = {}
        for f in fl:
            by[f.type] = by.get(f.type, 0) + 1

        unusual_count = sum(1 for s in an["stories"].values() if getattr(s, "outcome", "") == "unusual")
        raised_count = sum(1 for f in fl if not f.likely_benign)
        runtime_ms = int((time.time() - t0) * 1000)

        result_payload = {
            "job_id": job_id,
            "constituency_id": req_data.get("constituency_id", "AC005"),
            "flags": [f.model_dump(mode="json") for f in fl],
            "stories": [s.model_dump(mode="json") for s in an["stories"].values()],
            "by_type": by,
            "flags_total": len(fl),
            "flags_needing_review": raised_count,
            "runtime_ms": runtime_ms,
            "needs_human_review": True,
            "completed_at": _iso(time.time()),
        }

        # Save result JSON to disk
        result_file = _jobs_dir() / f"{job_id}.json"
        result_file.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")

        # Update job record
        with _LOCK:
            job.status = "completed"
            job.completed_at = time.time()
            job.runtime_ms = runtime_ms
            job.progress = JobProgress(stage="completed", percent=100, message="Constituency audit complete")
            job.summary = JobSummary(
                flags_total=len(fl),
                flags_needing_review=raised_count,
                stories_total=len(an["stories"]),
                unusual_booths=unusual_count,
                by_type=by,
                runtime_ms=runtime_ms,
            )
            _save_job_index()

    except Exception as e:
        log.exception("Audit job %s failed: %s", job_id, e)
        is_cancel = job_id in _CANCELLATIONS
        with _LOCK:
            job.status = "cancelled" if is_cancel else "failed"
            job.completed_at = time.time()
            job.runtime_ms = int((time.time() - t0) * 1000)
            job.error = str(e)
            job.progress = JobProgress(
                stage="cancelled" if is_cancel else "failed",
                percent=100,
                message=f"Job {'cancelled' if is_cancel else 'failed'}: {e}",
            )
            _save_job_index()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        _CANCELLATIONS.discard(job_id)


@router.post("/jobs/audit")
def submit_audit_job(req: AsyncAuditRequest, _=Depends(limits.rate("audit"))):
    """Submits an asynchronous constituency audit job and returns tracking details immediately."""
    total_len = sum(
        len(getattr(req, f) or "")
        for f in (
            "roll_v1_csv", "roll_v2_csv", "roll_v1_parquet_b64", "roll_v2_parquet_b64",
            "death_register_csv", "hostel_list_csv", "boundary_changes_csv"
        )
    )
    if total_len > limits.MAX_AUDIT * 2:  # allow 2x for async
        raise HTTPException(413, "Constituency rolls exceed allowed batch limit for async submission")

    if not (req.roll_v1_csv or req.roll_v1_parquet_b64):
        raise HTTPException(422, "roll_v1 missing (must provide roll_v1_csv or roll_v1_parquet_b64)")
    if not (req.roll_v2_csv or req.roll_v2_parquet_b64):
        raise HTTPException(422, "roll_v2 missing (must provide roll_v2_csv or roll_v2_parquet_b64)")

    now = time.time()
    job_id = f"job_{int(now)}_{os.urandom(4).hex()}"

    job = AuditJob(
        job_id=job_id,
        constituency_id=req.constituency_id,
        status="queued",
        created_at=now,
        progress=JobProgress(stage="queued", percent=0, message="Job queued in async background runner"),
    )

    token = secrets.token_urlsafe(24)
    with _LOCK:
        _JOBS[job_id] = job
        _JOB_TOKENS[job_id] = hashlib.sha256(token.encode("utf-8")).hexdigest()
        _save_job_index()

    req_dict = req.model_dump()
    _EXECUTOR.submit(_execute_audit_job, job_id, req_dict)

    return {
        "job_id": job_id,
        "constituency_id": req.constituency_id,
        "status": "queued",
        "job_token": token,  # send as X-Job-Token to see progress, fetch the result or cancel; shown once
        "check_url": f"/jobs/{job_id}",
        "result_url": f"/jobs/{job_id}/result",
        "created_at": _iso(now),
    }


@router.get("/jobs/{job_id}")
def get_audit_job(job_id: str, x_job_token: str | None = Header(None), x_wa_secret: str | None = Header(None)):
    """Returns the current execution state, stage, and progress of an audit job."""
    _authorize(job_id, x_job_token, x_wa_secret)
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return job.model_dump()


@router.get("/jobs/{job_id}/result")
def get_audit_job_result(job_id: str, x_job_token: str | None = Header(None), x_wa_secret: str | None = Header(None)):
    """Returns the completed audit results for a job."""
    _authorize(job_id, x_job_token, x_wa_secret)
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status == "running" or job.status == "queued":
        raise HTTPException(202, f"Job {job_id} is still {job.status}. Check {job.progress.percent}% progress.")
    if job.status == "failed" or job.status == "cancelled":
        raise HTTPException(400, f"Job {job_id} ended with status '{job.status}': {job.error}")

    res_file = _jobs_dir() / f"{job_id}.json"
    if not res_file.exists():
        raise HTTPException(404, "Result file not found on disk")

    try:
        return json.loads(res_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(500, f"Failed to read result file: {e}")


@router.get("/jobs")
def list_audit_jobs(
    status: str | None = None,
    constituency_id: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    x_wa_secret: str | None = Header(None),
):
    """Lists recent audit jobs (operator only: it would hand out other people's job ids)."""
    from api import wa_auth
    wa_auth._check_worker(x_wa_secret)
    with _LOCK:
        jobs = list(_JOBS.values())

    if status:
        jobs = [j for j in jobs if j.status == status]
    if constituency_id:
        jobs = [j for j in jobs if j.constituency_id.lower() == constituency_id.lower()]

    jobs.sort(key=lambda j: -j.created_at)
    return {"jobs": [j.model_dump() for j in jobs[:limit]], "total": len(jobs)}


@router.post("/jobs/{job_id}/cancel")
def cancel_audit_job(job_id: str, x_job_token: str | None = Header(None), x_wa_secret: str | None = Header(None)):
    """Requests cancellation of a queued or active audit job (submitter or operator)."""
    _authorize(job_id, x_job_token, x_wa_secret)
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(404, f"Job {job_id} not found")
        if job.status in ("completed", "failed", "cancelled"):
            return {"job_id": job_id, "status": job.status, "message": "Job already concluded"}

        _CANCELLATIONS.add(job_id)
        if job.status == "queued":
            job.status = "cancelled"
            job.completed_at = time.time()
            job.progress = JobProgress(stage="cancelled", percent=100, message="Cancelled while in queue")
            _save_job_index()

    return {"job_id": job_id, "status": "cancellation_requested"}
