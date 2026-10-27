"""Confidence (TRD 4.5): one Platt curve (logistic regression on a single feature) per flag type.

If a training district + its answer key are supplied (run.py --train-data/--train-key), curves are fit on the
engine's own flags there. Otherwise a documented heuristic mapping is used and confidence_n = 0.
Features: -log10(p of the leftover after innocent stories) for deletion spikes, -log10(q) for addition spikes, match score for duplicates, constant for deterministic rule flags.
Heuristic: spikes sigmoid(1.2 * (-log10 q - 1.3)) (q=0.05 -> 0.5, q=1e-3 -> 0.88); duplicates
sigmoid(25 * (score - 0.88)); rule flags fixed priors (impossible_age 0.9, oversized_household 0.6,
gender_ratio_swing 0.55, relation_conflict 0.5). A flag the engine cleared as likely benign is scaled by 0.3.
"""
from __future__ import annotations

import math
from typing import Any

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


# Types whose feature already says whether the evidence explains the flag (the leftover's p for deletion spikes),
# so they are fit on every flag, cleared ones included, and are not scaled again by BENIGN_SCALE.
TRAIN_WITH_BENIGN = {"deletion_spike"}


class Calibrator:
    def __init__(self):
        self.models: dict[str, tuple[LogisticRegression, int, float, float]] = {}
        self.recalibrated_reviews_count: int = 0
        self.last_recalibrated_at: str | None = None

    def fit(self, samples: dict[str, tuple[list[float], list[int]]], sample_weights: dict[str, list[float]] | None = None):
        """samples: type -> (features, labels 1 = true non-benign anomaly)."""
        for t, (x, y) in samples.items():
            if len(set(y)) < 2:
                continue
            # Standardised feature + C=1 (L2): the curve neither snaps to 0/1 on a few dozen flags nor goes flat
            # on a narrow feature range (match scores span only 0.88-1.0).
            xa = np.array(x, dtype=float)
            mu, sd = float(xa.mean()), float(xa.std()) or 1.0
            weights = np.array(sample_weights[t]) if (sample_weights and t in sample_weights) else None
            m = LogisticRegression(C=1.0).fit(((xa - mu) / sd).reshape(-1, 1), np.array(y), sample_weight=weights)
            self.models[t] = (m, len(y), mu, sd)
        return self

    def recalibrate_from_reviews(
        self,
        flags_by_id: dict[str, Any],
        audit_entries: list[Any],
        base_samples: dict[str, tuple[list[float], list[int]]] | None = None,
        reviewer_weight: float = 3.0
    ) -> dict[str, Any]:
        """Recalibrate Platt confidence curves incorporating human-reviewed verdicts.

        Maps 'escalated' reviews to true anomaly (1) and 'benign' reviews to cleared (0),
        weighting human expert reviews higher than synthetic baseline training cases.
        """
        import time
        from datetime import datetime, timezone

        samples = {k: (list(v[0]), list(v[1])) for k, v in (base_samples or {}).items()}
        weights: dict[str, list[float]] = {k: [1.0] * len(v[0]) for k, v in samples.items()}
        reviewed_counts: dict[str, int] = {}

        for entry in audit_entries:
            flag_id = getattr(entry, "flag_id", None) or (entry.get("flag_id") if isinstance(entry, dict) else None)
            action = getattr(entry, "action", "") or (entry.get("action", "") if isinstance(entry, dict) else "")
            if not flag_id or not action.startswith("review:") and not action.startswith("batch_review:"):
                continue

            verdict = action.split(":")[-1]
            if verdict not in ("escalated", "benign"):
                continue

            flag = flags_by_id.get(flag_id)
            if not flag:
                continue

            ftype = getattr(flag, "type", None) or (flag.get("type") if isinstance(flag, dict) else None)
            if not ftype:
                continue

            metrics = getattr(flag, "metrics", None) or (flag.get("metrics") if isinstance(flag, dict) else {})
            q_val = getattr(metrics, "q_value", None) if not isinstance(metrics, dict) else metrics.get("q_value")
            obs_val = getattr(metrics, "observed", None) if not isinstance(metrics, dict) else metrics.get("observed")

            feat = feature(ftype, q_val, obs_val)
            label = 1 if verdict == "escalated" else 0

            if ftype not in samples:
                samples[ftype] = ([], [])
                weights[ftype] = []

            samples[ftype][0].append(feat)
            samples[ftype][1].append(label)
            weights[ftype].append(reviewer_weight)
            reviewed_counts[ftype] = reviewed_counts.get(ftype, 0) + 1

        self.fit(samples, sample_weights=weights)
        self.recalibrated_reviews_count = sum(reviewed_counts.values())
        self.last_recalibrated_at = datetime.now(timezone.utc).isoformat()

        return {
            "status": "recalibrated",
            "reviewed_cases_incorporated": sum(reviewed_counts.values()),
            "by_type": reviewed_counts,
            "recalibrated_models": list(self.models.keys()),
            "timestamp": self.last_recalibrated_at,
        }

    def predict(self, ftype: str, x: float, likely_benign: bool = False) -> tuple[float, int]:
        if ftype in self.models:
            m, n, mu, sd = self.models[ftype]
            c = float(m.predict_proba(np.array([[(x - mu) / sd]]))[0, 1])
        else:
            c, n = heuristic(ftype, x), 0
        if likely_benign and not (ftype in TRAIN_WITH_BENIGN and ftype in self.models):
            c *= BENIGN_SCALE
        return float(min(max(c, 0.0), 1.0)), n

    def to_dict(self) -> dict[str, Any]:
        """Serialize calibrator model coefficients and intercept for inspection."""
        out = {}
        for t, (m, n, mu, sd) in self.models.items():
            out[t] = {
                "n_samples": n,
                "mean": mu,
                "std": sd,
                "coef": float(m.coef_[0, 0]),
                "intercept": float(m.intercept_[0]),
            }
        return {
            "models": out,
            "recalibrated_reviews_count": self.recalibrated_reviews_count,
            "last_recalibrated_at": self.last_recalibrated_at,
        }

