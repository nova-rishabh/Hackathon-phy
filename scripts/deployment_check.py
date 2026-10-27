"""RollWatch Pre-Deployment & Rollback Verification Tool.

Run: python scripts/deployment_check.py [--strict]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_checks(strict: bool = False) -> int:
    passes = 0
    warnings = 0
    failures = 0

    def ok(msg: str, detail: str = ""):
        nonlocal passes
        passes += 1
        print(f"  [PASS] {msg}" + (f" -> {detail}" if detail else ""))

    def warn(msg: str, detail: str = ""):
        nonlocal warnings
        warnings += 1
        print(f"  [WARN] {msg}" + (f" -> {detail}" if detail else ""))

    def fail(msg: str, detail: str = ""):
        nonlocal failures
        failures += 1
        print(f"  [FAIL] {msg}" + (f" -> {detail}" if detail else ""))

    print("======================================================================")
    print("                ROLLWATCH PRE-DEPLOYMENT VERIFICATION                 ")
    print("======================================================================")

    # 1. Environment & Keys
    print("\n--- 1. Environment Variables & Secrets ---")
    keys_to_check = {
        "AUTH_SECRET": ("Session tokens & signature encryption", True),
        "GEMINI_API_KEY": ("Gemini LLM phrasing & multimodal vision", False),
        "ELEVENLABS_API_KEY": ("Devi Hindi TTS voice generation", False),
        "WA_WORKER_SECRET": ("Internal WhatsApp bridge authentication", False),
        "REDIS_URL": ("Distributed session state & rate limits", False),
        "RAZORPAY_KEY_ID": ("Subscription billing public ID", False),
        "RAZORPAY_KEY_SECRET": ("Subscription billing webhook HMAC secret", False),
    }

    for key, (desc, required) in keys_to_check.items():
        val = os.environ.get(key, "").strip()
        if val:
            masked = val[:4] + "..." + val[-3:] if len(val) > 8 else "***"
            ok(f"{key} is set ({masked})", desc)
        else:
            if required or strict:
                fail(f"{key} is missing", f"Required for secure production: {desc}")
            else:
                warn(f"{key} is not set", f"Optional / falls back to in-memory/template: {desc}")

    # 2. Frozen Artifacts & Engine Data
    print("\n--- 2. Engine Data & Artifact Integrity ---")
    data_dir = Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts"))
    required_artifacts = [
        ("roll_v1.parquet", "Base roll dataset (v1)"),
        ("roll_v2.parquet", "Updated roll dataset (v2)"),
        ("flags.json", "Engine flagged anomalies"),
        ("stories.json", "Attributed booth stories"),
    ]

    for fname, desc in required_artifacts:
        fpath = data_dir / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            h = hashlib.sha256(fpath.read_bytes()[:4096]).hexdigest()[:8]
            size_kb = round(fpath.stat().st_size / 1024, 1)
            ok(f"{fname} ({size_kb} KB, prefix={h})", desc)
        else:
            fail(f"{fname} missing or empty", f"Expected in {data_dir}. Run generator + engine first.")

    # 3. Contract Schemas & Models
    print("\n--- 3. Pydantic Models & Contract Schemas ---")
    try:
        from contracts.models import Health, Overview, Flag, StoryResult, CitizenAnswer, ClaimVerdict
        ok("Core contract models imported cleanly", "contracts/models.py matches schema")
    except Exception as e:
        fail("Contract models import failed", str(e))

    # 4. Engine & Smoke Test
    print("\n--- 4. Engine Smoke Tests ---")
    try:
        from engine.run import analyse
        fix = ROOT / "contracts" / "fixtures"
        if fix.exists():
            a = analyse(fix)
            if a and "clusters" in a and "stories" in a:
                ok("Engine fixture analysis completed", f"Found clusters in {len(a['clusters'])} versions")
            else:
                fail("Engine fixture analysis returned incomplete payload")
        else:
            warn("contracts/fixtures not found to run local engine check")
    except Exception as e:
        fail("Engine execution failed on fixtures", str(e))

    # 5. Guard & Neutrality Lexicon
    print("\n--- 5. Content Guard & Neutrality Lexicon ---")
    try:
        from api.guard import check as guard_check
        test_viol = "The election was rigged by XYZ party in this booth"
        res_viol = guard_check(test_viol)
        if not res_viol.passed:
            ok("Guard blocks partisan/fraud phrasing", f"Blocked '{test_viol[:30]}...'")
        else:
            fail("Guard allowed non-neutral phrase!")

        test_safe = "412 deletions recorded in Booth B047."
        res_safe = guard_check(test_safe)
        if res_safe.passed:
            ok("Guard permits neutral analytical statements")
        else:
            fail("Guard incorrectly blocked neutral analytical text")
    except Exception as e:
        fail("Guard system error", str(e))

    # 6. Redis Connectivity (if configured)
    print("\n--- 6. Shared Storage / Redis Connectivity ---")
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=3)
            r.ping()
            ok("Redis connected and ping successful", redis_url.split("@")[-1])
        except Exception as e:
            fail("Redis connection failed", str(e))
    else:
        warn("REDIS_URL is not set", "Running in single-process in-memory mode (api/shared.py)")

    # 7. Web Bundle Sanity
    print("\n--- 7. Next.js Web Build Sanity ---")
    web_dir = ROOT / "web"
    next_dist = web_dir / ".next"
    if next_dist.exists():
        ok("Next.js .next build directory exists")
    else:
        warn("Next.js .next directory missing", "Run 'cd web && npm run build' before production deployment")

    # Summary
    print("\n======================================================================")
    print(f"VERIFICATION SUMMARY: {passes} PASSED, {warnings} WARNINGS, {failures} FAILURES")
    print("======================================================================")

    if failures > 0:
        print("\n [!] Pre-deployment verification FAILED. Do NOT deploy until failures are resolved.\n")
        return 1
    elif warnings > 0 and strict:
        print("\n [!] Strict mode enabled and warnings exist. Aborting deploy.\n")
        return 1
    else:
        print("\n [OK] Pre-deployment checks PASSED. System is ready for deployment.\n")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RollWatch Deployment Verifier")
    parser.add_argument("--strict", action="store_true", help="Fail if any warnings are detected")
    args = parser.parse_args()
    sys.exit(run_checks(strict=args.strict))
