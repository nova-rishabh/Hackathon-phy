"""'Try to fool RollWatch': hide extra removals in a booth and rerun the same tests the engine ran on the roll.

Works on the per-booth counts in artifacts/aggregates.json (voters, removed, unexplained, expected removals), so a
rerun across every booth takes milliseconds. Two tests, exactly as in engine.stats and engine.stories:
  spike    - removals vs the age-adjusted background, one-sided binomial, Benjamini-Hochberg across booths, q < 0.05
  residual - removals no record explains vs the same background, BH across booths that lost anyone, q < 0.05
A booth "needs human review" when the residual test fires (stories outcome "unusual").
"""
from __future__ import annotations

import numpy as np
from statsmodels.stats.multitest import multipletests

from .stats import p_greater

ALPHA = 0.05


def _bh(p: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """BH q-values; booths outside `mask` (no removals at all) are left out, as in engine.stories."""
    q = np.ones_like(p)
    idx = np.arange(len(p)) if mask is None else np.flatnonzero(mask)
    if len(idx):
        q[idx] = multipletests(p[idx], method="fdr_bh")[1]
    return q


class Booths:
    """Per-booth arrays from the aggregates: n voters (v1), removed, unexplained removals, expected removals."""

    def __init__(self, agg: dict):
        rows = [(b, x) for b, x in sorted(agg["booths"].items()) if x.get("n_v1")]
        self.ids = [b for b, _ in rows]
        self.pos = {b: i for i, b in enumerate(self.ids)}
        self.n = np.array([x["n_v1"] for _, x in rows], dtype=float)
        self.removed = np.array([x["removed"] for _, x in rows], dtype=float)
        self.unexplained = np.array([x.get("story_counts", {}).get("unexplained", x["removed"]) for _, x in rows], dtype=float)
        self.expected = np.array([x.get("expected_removed", 0.0) for _, x in rows], dtype=float)
        self.rate = np.divide(self.expected, self.n, out=np.zeros_like(self.n), where=self.n > 0)

    def run(self, removed: np.ndarray, unexplained: np.ndarray) -> dict:
        p_sp = p_greater(removed, self.n, self.rate)
        p_re = p_greater(unexplained, self.n, self.rate)
        return {"p_spike": p_sp, "q_spike": _bh(p_sp), "p_res": p_re, "q_res": _bh(p_re, removed > 0)}

    def plant(self, booths: list[str], k: int, with_record: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Remove k names in total, split as evenly as the booths allow (never more than a booth has)."""
        extra = np.zeros_like(self.n)
        idx = [self.pos[b] for b in booths]
        room = self.n[idx] - self.removed[idx]
        share = np.full(len(idx), k // len(idx)) + (np.arange(len(idx)) < k % len(idx))
        extra[idx] = np.minimum(share, room)
        rem = self.removed + extra
        un = self.unexplained + (0 if with_record else extra)
        return rem, un, extra


def _verdict(t: dict, i: int) -> str:
    if t["q_res"][i] < ALPHA:
        return "caught"  # needs human review
    if t["q_spike"][i] < ALPHA:
        return "flagged"  # the spike fires but the leftover is not unusual (yet): shown, not sent to review
    return "missed"


def simulate(bs: Booths, booth: str, k: int, with_record: bool = False, spread: int = 1) -> dict:
    """Hide k extra removals starting at `booth` (spread over `spread` consecutive booths) and rerun both tests."""
    if booth not in bs.pos:
        raise KeyError(booth)
    spread = max(1, min(int(spread), len(bs.ids)))
    start = bs.pos[booth]
    targets = [bs.ids[(start + j) % len(bs.ids)] for j in range(spread)]
    k = max(0, int(k))
    base = bs.run(bs.removed, bs.unexplained)
    rem, un, extra = bs.plant(targets, k, with_record)
    t = bs.run(rem, un)
    rows = []
    for b in targets:
        i = bs.pos[b]
        rows.append({"booth_id": b, "n": int(bs.n[i]), "hidden": int(extra[i]),
                     "removed_before": int(bs.removed[i]), "removed_after": int(rem[i]),
                     "unexplained_after": int(un[i]), "expected": round(float(bs.expected[i]), 1),
                     "p_spike": float(t["p_spike"][i]), "q_spike": float(t["q_spike"][i]),
                     "p_residual": float(t["p_res"][i]), "q_residual": float(t["q_res"][i]),
                     "verdict": _verdict(t, i), "verdict_before": _verdict(base, i)})
    # Count only what the hidden names changed: a booth already under review on the real roll is not a catch.
    caught = sum(r["verdict"] == "caught" and r["verdict_before"] != "caught" for r in rows)
    flagged = sum(r["verdict"] != "missed" and r["verdict"] != r["verdict_before"] for r in rows)  # newly noticed, incl. caught
    already = sum(r["verdict_before"] != "missed" and r["verdict"] == r["verdict_before"] for r in rows)
    # Rank of the first target among all booths by residual q (1 = most unusual), so "how loud" is visible.
    i0 = bs.pos[targets[0]]
    rank = int(1 + np.sum(t["q_res"] < t["q_res"][i0]))
    others_flipped = [bs.ids[j] for j in range(len(bs.ids))
                      if bs.ids[j] not in targets and _verdict(t, j) != _verdict(base, j)]
    return {"booth_id": booth, "hidden_total": int(extra.sum()), "with_record": bool(with_record), "spread": spread,
            "booths": rows, "caught": caught, "flagged": flagged, "already_flagged": already, "rank": rank, "n_booths": len(bs.ids),
            "others_changed": others_flipped, "limit": detection_limit(bs, booth, with_record=False),
            "alpha": ALPHA}


def detection_limit(bs: Booths, booth: str, with_record: bool = False) -> int | None:
    """Smallest number of hidden removals (no record) that this booth's tests would send to human review,
    with every other booth as it is. None if no amount up to the booth's size is caught."""
    i = bs.pos[booth]
    base = bs.run(bs.removed, bs.unexplained)
    if base["q_res"][i] < ALPHA:
        return 0  # already needs review on the real roll
    hi = int(bs.n[i] - bs.removed[i])

    def caught(k: int) -> bool:
        rem, un, _ = bs.plant([booth], k, with_record)
        return bs.run(rem, un)["q_res"][i] < ALPHA

    if hi <= 0 or not caught(hi):
        return None
    lo = 0  # caught(lo) is False, caught(hi) is True: binary search for the first k that is caught
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if caught(mid) else (mid, hi)
    return hi


def limits(bs: Booths) -> dict:
    """Detection limit for every booth (booths already under review report 0)."""
    out = {b: detection_limit(bs, b) for b in bs.ids}
    vals = [v for v in out.values() if v]
    share = [v / bs.n[bs.pos[b]] for b, v in out.items() if v]
    return {"by_booth": out, "median": int(np.median(vals)) if vals else None,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "median_share_of_booth": round(float(np.median(share)), 4) if share else None,
            "already_under_review": sorted(b for b, v in out.items() if v == 0)}
