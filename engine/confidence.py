"""Confidence (TRD 4.5): one Platt curve (logistic regression on a single feature) per flag type.

If a training district + its answer key are supplied (run.py --train-data/--train-key), curves are fit on the
engine's own flags there. Otherwise a documented heuristic mapping is used and confidence_n = 0.
Features: -log10(q) for spikes, match score for duplicates, constant for deterministic rule flags.
Heuristic: spikes sigmoid(1.2 * (-log10 q - 1.3)) (q=0.05 -> 0.5, q=1e-3 -> 0.88); duplicates
sigmoid(25 * (score - 0.88)); rule flags fixed priors (impossible_age 0.9, oversized_household 0.6,
gender_ratio_swing 0.55, relation_conflict 0.5). A flag whose story outcome is likely_benign is scaled by 0.3.
"""
from __future__ import annotations

import math

import numpy as np
from sklearn.linear_model import LogisticRegression

HEURISTIC_PRIOR = {"impossible_age": 0.9, "oversized_household": 0.6, "gender_ratio_swing": 0.55, "relation_conflict": 0.5}
BENIGN_SCALE = 0.3


def band_of(c: float) -> str:
    return "low" if c < 0.5 else ("medium" if c < 0.8 else "high")


def feature(ftype: str, q: float | None, score: float | None) -> float:
    if ftype in ("deletion_spike", "addition_spike"):
        return float(min(-math.log10(max(q if q is not None else 1.0, 1e-12)), 12.0))
    if ftype == "duplicate_cluster":
        return float(score or 0.0)
    return 1.0


def _sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def heuristic(ftype: str, x: float) -> float:
    if ftype in ("deletion_spike", "addition_spike"):
        return _sig(1.2 * (x - 1.3))
    if ftype == "duplicate_cluster":
        return _sig(25.0 * (x - 0.88))
    return HEURISTIC_PRIOR.get(ftype, 0.5)


class Calibrator:
    def __init__(self):
        self.models: dict[str, tuple[LogisticRegression, int]] = {}

    def fit(self, samples: dict[str, tuple[list[float], list[int]]]):
        """samples: type -> (features, labels 1 = true non-benign anomaly)."""
        for t, (x, y) in samples.items():
            if len(set(y)) < 2:
                continue
            m = LogisticRegression(C=1e6).fit(np.array(x).reshape(-1, 1), np.array(y))
            self.models[t] = (m, len(y))
        return self

    def predict(self, ftype: str, x: float, likely_benign: bool = False) -> tuple[float, int]:
        if ftype in self.models:
            m, n = self.models[ftype]
            c = float(m.predict_proba(np.array([[x]]))[0, 1])
        else:
            c, n = heuristic(ftype, x), 0
        if likely_benign:
            c *= BENIGN_SCALE
        return float(min(max(c, 0.0), 1.0)), n
