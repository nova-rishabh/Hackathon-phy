"""RollWatch smoke checks (TRD section 9). Run: python smoke_test.py  (against contracts/fixtures/).

Check 1 and 2 belong to A2 (engine). Checks 3-5 are added by other sessions at the placeholders below.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
FIX = ROOT / "contracts" / "fixtures"
EXPECTED = json.loads((FIX / "expected.json").read_text(encoding="utf-8"))
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def engine_checks():
    from engine.run import analyse
    a = analyse(FIX)
    # 1. cross-script duplicate cluster found
    found = [sorted(c["voter_ids"]) for ver in ("v1", "v2") for c in a["clusters"][ver]]
    for want in EXPECTED["duplicate_clusters"]:
        check("1 cross-script duplicate clustered", sorted(want) in found, f"found={found}")
    # 2. booth B002 likely_benign + per-record story attribution
    st = a["stories"]
    for booth, want in EXPECTED["booth_outcomes"].items():
        check(f"2 booth {booth} outcome", st[booth].outcome == want, f"got {st[booth].outcome}")
    got = per_record_story(a, a["data"])
    for vid, want in EXPECTED["story_attribution"].items():
        check(f"2 story {vid}", got.get(vid) == want, f"got {got.get(vid)} want {want}")


def per_record_story(a, d):
    from engine.stories import attribute_records
    tables = {"death_register": d.death, "hostel_list": d.hostel, "boundary_changes": d.boundary}
    return attribute_records(d.v1, d.v2, tables, a["clusters"]["v1"])


def api_checks():
    """Checks 3-5 (owner: A1)."""
    from api.guard import check as guard_check
    bad = ["The roll was rigged in this booth", "A party worker from BJP did this", "Kejriwal removed these names",
           "बूथ में धांधली हुई", "ਇਹ ਵੋਟ ਚੋਰੀ ਹੈ"]
    for s in bad:
        check(f"3 guard blocks: {s[:24]}", not guard_check(s).passed)
    check("3 guard passes neutral text", guard_check("412 records were removed in Booth B047.").passed)
    from api.claims import verdict_of
    got = [verdict_of(100, 105)[0], verdict_of(600, 412)[0], verdict_of(None, 412)[0]]
    check("4 claim verdict rule", got == ["verified", "disputed", "unprovable"], f"got {got}")
    if not (ROOT / "artifacts" / "roll_v2.parquet").exists():
        check("5 API /overview 100 booths", False, "artifacts/ missing: run the generator + engine first")
        return
    os.environ.setdefault("ROLLWATCH_DATA", str(ROOT / "artifacts"))
    from fastapi.testclient import TestClient
    from api.main import app
    r = TestClient(app).get("/overview")
    n = len(r.json().get("booths", [])) if r.status_code == 200 else 0
    check("5 API /overview 100 booths", n == 100, f"status={r.status_code} booths={n}")


if __name__ == "__main__":
    engine_checks()
    api_checks()
    print("FAILED: " + ", ".join(FAILS) if FAILS else "ALL PASSED")
    sys.exit(1 if FAILS else 0)
