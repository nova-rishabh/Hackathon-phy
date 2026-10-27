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
    from engine.stories import attribute  # noqa: F401  (attribution is exercised via per-record check below)
    d = a["data"]
    from engine.dupes import norm  # noqa: F401
    got = per_record_story(a, d)
    for vid, want in EXPECTED["story_attribution"].items():
        check(f"2 story {vid}", got.get(vid) == want, f"got {got.get(vid)} want {want}")


def per_record_story(a, d):
    from engine import stories as S
    from engine.stories import _int, norm
    v2_booth = dict(zip(d.v2.voter_id, d.v2.booth_id))
    ids2 = set(v2_booth)
    cl = {m: c["voter_ids"] for c in a["clusters"]["v1"] for m in c["voter_ids"]}
    death = {}
    for r in d.death.itertuples():
        death.setdefault((r.booth_id, str(r.house_no)), []).append((norm(r.name_lat), int(r.age)))
    host = {(r.booth_id, str(r.house_no)) for r in d.hostel.itertuples()}
    bnd = [(r.from_booth, r.to_booth, _int(r.house_from), _int(r.house_to)) for r in d.boundary.itertuples()]
    out = {}
    removed = d.v1[(~d.v1.voter_id.isin(ids2)) | (d.v1.voter_id.map(v2_booth).fillna("") != d.v1.booth_id)]
    for r in removed.itertuples():
        out[r.voter_id] = S.attribute(r, v2_booth, ids2, cl, death, host, bnd, set(S.ALL_CONTEXT))
    return out


# PLACEHOLDER check 3: neutrality guard blocks 5 seeded bad strings (owner: guard session)
# PLACEHOLDER check 4: claim verdict rule maps claimed vs computed (owner: claims session)
# PLACEHOLDER check 5: API boots and /overview returns 100 booths (owner: api session)

if __name__ == "__main__":
    engine_checks()
    print("FAILED: " + ", ".join(FAILS) if FAILS else "ALL PASSED")
    sys.exit(1 if FAILS else 0)
