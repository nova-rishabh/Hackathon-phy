"""'Which Story Fits?' (TRD 4.2): deterministic attribution, bootstrap CI, residual test.

Story order and match keys live in engine/stories.yaml (PRD S12). A new evidence source is one YAML entry
using an existing match kind (MATCHERS below); no code change.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from rapidfuzz.distance import JaroWinkler
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

from contracts.models import Residual, Story, StoryResult

from .dupes import norm
from .stats import band

CONFIG_PATH = Path(__file__).with_name("stories.yaml")
CONTRACT_CODES = {"death_registered", "hostel_moveout", "boundary_change", "duplicate_cleanup", "unexplained"}
CONTRACT_CONTEXT = {"death_register", "hostel_list", "boundary_changes", "duplicates"}


@lru_cache(maxsize=8)
def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: str | Path | None = None) -> dict:
    return _load(str(path or CONFIG_PATH))


def _cfg(config) -> dict:
    return config if isinstance(config, dict) else load_config(config)


def all_context(config=None) -> list[str]:
    return [s["context"] for s in _cfg(config)["sources"]]


def codes(config=None) -> list[str]:
    c = _cfg(config)
    return [s["code"] for s in c["sources"]] + [c["unexplained"]["code"]]


def labels(config=None) -> dict[str, str]:
    c = _cfg(config)
    return {s["code"]: s["label"] for s in c["sources"]} | {c["unexplained"]["code"]: c["unexplained"]["label"]}


ALL_CONTEXT = all_context()
CODES = codes()
LABELS = labels()


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ matchers
# Each factory takes (spec, table, state) and returns fn(rec) -> bool. state: v2_booth, v2_ids, clusters.

def _name_in_house(spec, table, state):
    name_col, age_col = spec.get("name_col", "name_lat"), spec.get("age_col")
    tol, sim = spec.get("age_tol", 2), spec.get("name_sim", 0.93)
    idx: dict = {}
    for r in table.to_dict("records"):
        age = _int(r.get(age_col)) if age_col else None
        if age_col and age is None:
            continue
        idx.setdefault((str(r["booth_id"]), str(r["house_no"])), []).append((norm(str(r[name_col])), age))

    def f(rec):
        cands = idx.get((rec.booth_id, rec.house_no))
        if not cands:
            return False
        nm = norm(rec.name_lat)
        return any((age is None or abs(age - rec.age) <= tol) and (name == nm or JaroWinkler.similarity(name, nm) >= sim)
                   for name, age in cands)
    return f


def _duplicate_survivor(spec, table, state):
    cl, v2_ids = state["clusters"], state["v2_ids"]
    return lambda rec: any(m != rec.voter_id and m in v2_ids for m in cl.get(rec.voter_id, ()))


def _house_range_moved(spec, table, state):
    rows = [(str(r["from_booth"]), str(r["to_booth"]), _int(r["house_from"]), _int(r["house_to"]))
            for r in table.to_dict("records")]
    v2_booth = state["v2_booth"]

    def f(rec):
        h = _int(rec.house_no)
        return h is not None and any(fb == rec.booth_id and lo is not None and lo <= h <= hi and v2_booth.get(rec.voter_id) == tb
                                     for fb, tb, lo, hi in rows)
    return f


def _house_listed(spec, table, state):
    keys = {(str(r["booth_id"]), str(r["house_no"])) for r in table.to_dict("records")}
    lo, hi = spec.get("age_min", 0), spec.get("age_max", 200)
    return lambda rec: (rec.booth_id, rec.house_no) in keys and lo <= rec.age <= hi


MATCHERS = {"name_in_house": _name_in_house, "duplicate_survivor": _duplicate_survivor,
            "house_range_moved": _house_range_moved, "house_listed": _house_listed}


def load_tables(data_dir, config=None) -> dict[str, pd.DataFrame]:
    """context name -> table for every YAML source that names a file (missing file = empty table)."""
    d = Path(data_dir)
    dirs = [d, d / "context", d / "artifacts" / "context"]
    out = {}
    for s in _cfg(config)["sources"]:
        if not s.get("file"):
            continue
        p = next((x / s["file"] for x in dirs if (x / s["file"]).exists()), None)
        out[s["context"]] = pd.read_csv(p, dtype=str, encoding="utf-8", keep_default_na=False) if p else pd.DataFrame()
    return out


def removed_set(v1: pd.DataFrame, v2_booth: dict) -> pd.DataFrame:
    """v1 records gone from v2, or now listed in a different booth."""
    return v1[v1.voter_id.map(v2_booth).fillna("") != v1.booth_id]


def attribute_records(v1, v2, tables: dict, clusters_v1: list[dict], context_on=None, config=None) -> dict[str, str]:
    """voter_id -> story code for every removed record (first matching source in YAML order)."""
    cfg = _cfg(config)
    ctx = set(all_context(cfg) if context_on is None else context_on)
    v2_booth = dict(zip(v2.voter_id, v2.booth_id))
    state = {"v2_booth": v2_booth, "v2_ids": set(v2_booth),
             "clusters": {m: c["voter_ids"] for c in clusters_v1 for m in c["voter_ids"]}}
    matchers = []
    for s in cfg["sources"]:
        if s["context"] not in ctx:
            continue
        tbl = tables.get(s["context"], pd.DataFrame())
        if s.get("file") and tbl.empty:
            continue
        matchers.append((s["code"], MATCHERS[s["match"]["kind"]](s["match"], tbl, state)))
    un = cfg["unexplained"]["code"]
    return {rec.voter_id: next((c for c, f in matchers if f(rec)), un) for rec in removed_set(v1, v2_booth).itertuples()}


def _mk(model, strict: bool, **kw):
    return model(**kw) if strict else model.model_construct(**kw)


def compute_stories(v1: pd.DataFrame, v2: pd.DataFrame, death: pd.DataFrame | None, hostel: pd.DataFrame | None,
                    boundary: pd.DataFrame | None, clusters_v1: list[dict], rates: np.ndarray,
                    context_on: list[str] | None = None, seed: int = 42, n_boot: int = 500,
                    tables: dict[str, pd.DataFrame] | None = None, config=None) -> dict[str, StoryResult]:
    """StoryResult for every booth with at least one removed record. `context_on` switches context tables
    on/off (the live toggle); default all on. Extra YAML sources pass their tables via `tables`.
    Sources whose code/context is outside the contracts Literals are built unvalidated (model_construct)."""
    cfg = _cfg(config)
    tbls = dict(tables or {})
    for k, t in (("death_register", death), ("hostel_list", hostel), ("boundary_changes", boundary)):
        if t is not None and k not in tbls:
            tbls[k] = t
    ctx_all = all_context(cfg)
    ctx = set(ctx_all if context_on is None else context_on)
    code_list, lab = codes(cfg), labels(cfg)
    un_code = cfg["unexplained"]["code"]
    strict = set(code_list) <= CONTRACT_CODES and set(ctx_all) <= CONTRACT_CONTEXT

    attr = attribute_records(v1, v2, tbls, clusters_v1, context_on=list(ctx), config=cfg)
    if not attr:
        return {}
    ci = {c: i for i, c in enumerate(code_list)}
    rem = pd.DataFrame({"voter_id": list(attr), "k": [ci[c] for c in attr.values()]})
    rem["booth_id"] = rem.voter_id.map(dict(zip(v1.voter_id, v1.booth_id)))
    n_by_booth = v1.groupby("booth_id").size()
    exp_by_booth = v1.assign(p=v1.age.map(band).map(lambda i: rates[i])).groupby("booth_id").p.sum()
    rng = np.random.default_rng(seed)
    K = len(code_list)

    per = {}
    for booth, grp in rem.groupby("booth_id", sort=True):
        arr = grp.k.to_numpy()
        n = len(arr)
        samp = arr[rng.integers(0, n, size=(n_boot, n))]  # vectorised bootstrap: B x n
        boot = np.stack([(samp == k).mean(axis=1) for k in range(K)], axis=1)
        lo, hi = np.percentile(boot, 5, axis=0), np.percentile(boot, 95, axis=0)
        counts = np.bincount(arr, minlength=K)
        nb, ex = int(n_by_booth[booth]), float(exp_by_booth[booth])
        un = int(counts[ci[un_code]])
        p = float(binomtest(un, nb, min(max(ex / nb, 1e-9), 1 - 1e-9), alternative="greater").pvalue)
        per[booth] = (n, counts, lo, hi, un, ex, p)

    booths = list(per)
    qs = multipletests([per[b][6] for b in booths], method="fdr_bh")[1]
    out = {}
    for b, q in zip(booths, qs):
        n, counts, lo, hi, un, ex, p = per[b]
        stories = []
        for i, c in enumerate(code_list):
            ev = f"{int(counts[i])} of {n} removed records" + (
                "" if c == un_code else f" matched using {'the ' + c.replace('_', ' ') + ' evidence'}")
            stories.append(_mk(Story, strict, code=c, label=lab[c], count=int(counts[i]), share=float(counts[i] / n),
                               ci_lo=float(lo[i]), ci_hi=float(hi[i]), evidence=ev))
        significant = bool(q < 0.05)
        top_innocent = max(s.share for s in stories if s.code != un_code)
        outcome = "unusual" if significant else ("likely_benign" if top_innocent >= 0.6 else "mixed")
        out[b] = _mk(StoryResult, strict,
                     booth_id=b, removed_total=n, stories=stories,
                     residual=Residual(count=un, expected_background=ex, p_value=p, significant=significant),
                     context_used=[c for c in ctx_all if c in ctx], outcome=outcome)
    return out
