"""'Which Story Fits?' (TRD 4.2): deterministic attribution, bootstrap CI, residual test."""
from __future__ import annotations

import numpy as np
import pandas as pd
from rapidfuzz.distance import JaroWinkler
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

from contracts.models import Residual, Story, StoryResult

from .dupes import norm
from .stats import band

CODES = ["death_registered", "duplicate_cleanup", "boundary_change", "hostel_moveout", "unexplained"]
LABELS = {
    "death_registered": "Matches a death-register entry",
    "duplicate_cleanup": "Duplicate cleaned up (another copy remains)",
    "boundary_change": "House moved to another booth",
    "hostel_moveout": "Hostel move-out (academic year end)",
    "unexplained": "Unexplained by any available record",
}
ALL_CONTEXT = ["death_register", "hostel_list", "boundary_changes", "duplicates"]
CTX_ORDER = ["death_register", "duplicates", "boundary_changes", "hostel_list"]


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def attribute(rec, v2_booth: dict, v2_ids: set, clusters_v1: dict, death_idx: dict, hostel: set,
              boundary: list, ctx: set) -> str:
    """First matching story, in the TRD order."""
    if "death_register" in ctx:
        nm = norm(rec.name_lat)
        for name, age in death_idx.get((rec.booth_id, rec.house_no), []):
            if abs(age - rec.age) <= 2 and (name == nm or JaroWinkler.similarity(name, nm) >= 0.93):
                return "death_registered"
    if "duplicates" in ctx:
        others = [m for m in clusters_v1.get(rec.voter_id, []) if m != rec.voter_id]
        if any(m in v2_ids for m in others):
            return "duplicate_cleanup"
    if "boundary_changes" in ctx:
        h = _int(rec.house_no)
        if h is not None:
            for fb, tb, lo, hi in boundary:
                if fb == rec.booth_id and lo <= h <= hi and v2_booth.get(rec.voter_id) == tb:
                    return "boundary_change"
    if "hostel_list" in ctx and (rec.booth_id, rec.house_no) in hostel and 18 <= rec.age <= 25:
        return "hostel_moveout"
    return "unexplained"


def compute_stories(v1: pd.DataFrame, v2: pd.DataFrame, death: pd.DataFrame, hostel: pd.DataFrame,
                    boundary: pd.DataFrame, clusters_v1: list[dict], rates: np.ndarray,
                    context_on: list[str] | None = None, seed: int = 42, n_boot: int = 500) -> dict[str, StoryResult]:
    """StoryResult for every booth with at least one removed record. `context_on` switches context tables
    on/off (the live toggle); default all on."""
    ctx = set(ALL_CONTEXT if context_on is None else context_on)
    v2_booth = dict(zip(v2.voter_id, v2.booth_id))
    v2_ids = set(v2_booth)
    cl = {}
    for c in clusters_v1:
        for m in c["voter_ids"]:
            cl[m] = c["voter_ids"]
    death_idx: dict = {}
    for r in death.itertuples():
        a = _int(r.age)
        if a is not None:
            death_idx.setdefault((r.booth_id, str(r.house_no)), []).append((norm(r.name_lat), a))
    host = {(r.booth_id, str(r.house_no)) for r in hostel.itertuples()}
    bnd = [(r.from_booth, r.to_booth, _int(r.house_from), _int(r.house_to)) for r in boundary.itertuples()]

    removed = v1[(~v1.voter_id.isin(v2_ids)) | (v1.voter_id.map(v2_booth).fillna("") != v1.booth_id)]
    n_by_booth = v1.groupby("booth_id").size()
    exp_by_booth = v1.assign(p=v1.age.map(band).map(lambda i: rates[i])).groupby("booth_id").p.sum()
    rng = np.random.default_rng(seed)

    per = {}
    for booth, grp in removed.groupby("booth_id"):
        codes = [attribute(r, v2_booth, v2_ids, cl, death_idx, host, bnd, ctx) for r in grp.itertuples()]
        n = len(codes)
        arr = np.array([CODES.index(c) for c in codes])
        boot = np.array([np.bincount(rng.choice(arr, n), minlength=len(CODES)) / n for _ in range(n_boot)])
        lo, hi = np.percentile(boot, 5, axis=0), np.percentile(boot, 95, axis=0)
        counts = np.bincount(arr, minlength=len(CODES))
        nb, ex = int(n_by_booth[booth]), float(exp_by_booth[booth])
        un = int(counts[CODES.index("unexplained")])
        p = float(binomtest(un, nb, min(max(ex / nb, 1e-9), 1 - 1e-9), alternative="greater").pvalue)
        per[booth] = (n, counts, lo, hi, un, ex, p)

    booths = list(per)
    qs = multipletests([per[b][6] for b in booths], method="fdr_bh")[1] if booths else []
    out = {}
    for b, q in zip(booths, qs):
        n, counts, lo, hi, un, ex, p = per[b]
        stories = []
        for i, c in enumerate(CODES):
            ev = f"{int(counts[i])} of {n} removed records" + (
                "" if c == "unexplained" else f" matched using {'the ' + c.replace('_', ' ') + ' evidence'}")
            stories.append(Story(code=c, label=LABELS[c], count=int(counts[i]), share=float(counts[i] / n),
                                 ci_lo=float(lo[i]), ci_hi=float(hi[i]), evidence=ev))
        significant = bool(q < 0.05)
        top_innocent = max(s.share for s in stories if s.code != "unexplained")
        outcome = "unusual" if significant else ("likely_benign" if top_innocent >= 0.6 else "mixed")
        out[b] = StoryResult(
            booth_id=b, removed_total=n, stories=stories,
            residual=Residual(count=un, expected_background=ex, p_value=p, significant=significant),
            context_used=[c for c in CTX_ORDER if c in ctx], outcome=outcome)
    return out
