"""Booth deletion/addition tests (TRD 4.1)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

BANDS = [(0, 24), (25, 34), (35, 44), (45, 59), (60, 74), (75, 200)]


def band(age: int) -> int:
    for i, (_, hi) in enumerate(BANDS):
        if age <= hi:
            return i
    return len(BANDS) - 1


def _p(obs: float, n: int, p0: float) -> float:
    if n <= 0:
        return 1.0
    return float(binomtest(int(obs), int(n), float(min(max(p0, 1e-9), 1 - 1e-9)), alternative="greater").pvalue)


def band_rates(v1: pd.DataFrame, v2: pd.DataFrame) -> np.ndarray:
    """District background removal rate per age band. Stand-in for the generator's churn model
    (age-specific mortality shape plus a migration rate), estimated from the district itself. Booths whose
    raw test is extreme (p<0.01) are excluded and rates refit, so a spike does not inflate its own background."""
    d = v1.assign(b=v1.age.map(band), gone=~v1.voter_id.isin(set(v2.voter_id)))

    def rates(frame):
        g = frame.groupby("b").gone.agg(["sum", "size"]).reindex(range(len(BANDS))).fillna(0)
        overall = frame.gone.mean() if len(frame) else 0.0
        return np.where(g["size"] > 0, g["sum"] / g["size"].clip(lower=1), overall)

    r = rates(d)
    exp = d.assign(p=d.b.map(lambda i: r[i])).groupby("booth_id").p.sum()
    obs = d.groupby("booth_id").gone.sum()
    n = d.groupby("booth_id").size()
    keep = [b for b in n.index if _p(obs[b], n[b], exp[b] / n[b]) >= 0.01]
    if keep and len(keep) < len(n):
        r = rates(d[d.booth_id.isin(keep)])
    return np.maximum(r, 1e-6)


def booth_tests(v1: pd.DataFrame, v2: pd.DataFrame, rates: np.ndarray) -> pd.DataFrame:
    """One row per booth: deletions (id absent from v2) and additions (id absent from v1),
    each with observed/expected/p/q (binomtest greater + Benjamini-Hochberg across booths)."""
    ids1, ids2 = set(v1.voter_id), set(v2.voter_id)
    d1 = v1.assign(gone=~v1.voter_id.isin(ids2))
    d1["p"] = d1.age.map(band).map(lambda i: rates[i])
    g = d1.groupby("booth_id").agg(n_v1=("voter_id", "size"), del_obs=("gone", "sum"), del_exp=("p", "sum"))
    d2 = v2.assign(new=~v2.voter_id.isin(ids1))
    g2 = d2.groupby("booth_id").agg(n_v2=("voter_id", "size"), add_obs=("new", "sum"))
    g = g.join(g2, how="outer").fillna(0)
    g["add_exp"] = g.n_v2 * (g.add_obs.sum() / max(g.n_v2.sum(), 1))
    for kind, n in (("del", "n_v1"), ("add", "n_v2")):
        ps = [_p(r[kind + "_obs"], r[n], r[kind + "_exp"] / r[n] if r[n] else 0) for _, r in g.iterrows()]
        g[kind + "_p"] = ps
        g[kind + "_q"] = list(multipletests(ps, method="fdr_bh")[1]) if ps else []
    return g
