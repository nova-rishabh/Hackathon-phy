"""Artifacts held in memory (ROLLWATCH_DATA, default artifacts/) + precomputed O(1) claim aggregates."""
from __future__ import annotations

import json
import os
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.models import (BoothSummary, Card, EvalResult, Flag, Overview, RuleCard, StoryResult, Totals)
from engine.data import load as load_data
from engine.diff import diff
from engine.stats import BANDS, band_rates, booth_tests
from engine.stories import compute_stories

ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    p = Path(os.environ.get("ROLLWATCH_DATA", ROOT / "artifacts"))
    return p if p.is_absolute() else ROOT / p


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _card(f: Flag) -> Card | None:
    """Template flag card (numbers from the engine; phrasing fixed)."""
    m, b = f.metrics, f.scope.booth_id
    conf = f"Confidence {round(f.confidence * 100)}% ({f.confidence_band}, from {f.confidence_n} training cases). Needs human review."
    if f.type == "deletion_spike":
        st = f.stories
        innocent = []
        if st:
            for s in st.stories:
                if s.code != "unexplained" and s.count:
                    innocent.append(f"{s.label}: {s.count} of {st.removed_total} ({round(s.share * 100)}%)")
            un = next((s for s in st.stories if s.code == "unexplained"), None)
            why = (f"{int(m.observed)} removed against about {round(m.expected or 0)} expected for this booth's ages. "
                   f"{un.count if un else 0} ({round((un.share if un else 0) * 100)}%) are not explained by any record.")
        else:
            why = f"{int(m.observed)} removed against about {round(m.expected or 0)} expected for this booth's ages."
        return Card(found=f"Booth {b}: {int(m.observed)} of {m.n} records removed between versions.",
                    why_unusual=why, innocent_explanations=innocent or ["No context record matches these removals."],
                    confidence_text=conf, lang="en", source="template")
    if f.type == "addition_spike":
        return Card(found=f"Booth {b}: {int(m.observed)} records added between versions.",
                    why_unusual=f"About {round(m.expected or 0)} additions were expected at the district rate.",
                    innocent_explanations=["New housing or a new colony in the booth area",
                                           "A registration drive (for example, first-time voters turning 18)",
                                           "Records moved in by a boundary change"],
                    confidence_text=conf, lang="en", source="template")
    return None


class Store:
    def __init__(self, d: Path):
        self.dir = d
        self.data = load_data(d)
        v1, v2 = self.data.v1, self.data.v2
        self.rates = band_rates(v1, v2)
        self.tests = booth_tests(v1, v2, self.rates)
        self.diff = diff(v1, v2)
        raw_flags = _read_json(d / "flags.json") or []
        self.flags = [Flag.model_validate(x) for x in raw_flags]
        self._fill_cards()
        self.flag_by_id = {f.flag_id: f for f in self.flags}
        self.stories = {s["booth_id"]: StoryResult.model_validate(s) for s in (_read_json(d / "stories.json") or [])}
        self.clusters_v1 = [{"voter_ids": f.scope.voter_ids} for f in self.flags if f.type == "duplicate_cluster"]
        self.rules = _read_json(d / "rules.json")
        self.eval = _read_json(d / "eval.json")
        self._toggle_cache: dict[tuple, dict] = {}
        self._lock = threading.Lock()
        self._agg()

    def _fill_cards(self):
        from api.guard import guard
        for f in self.flags:
            if f.card is None and f.type in ("deletion_spike", "addition_spike"):
                c = _card(f)
                if c:
                    res = None
                    for fld in ("found", "why_unusual", "confidence_text"):
                        txt, res = guard(getattr(c, fld), "flag_card", "en")
                        setattr(c, fld, txt)
                    f.card, f.guard = c, res

    # ---------------------------------------------------------- aggregates (claim tools, overview)
    def _agg(self):
        v1, v2, t = self.data.v1, self.data.v2, self.tests
        booths = sorted(set(v1.booth_id) | set(v2.booth_id))
        t = t.reindex(booths).fillna(0)
        self.booths = booths
        self.ward = {**dict(zip(v2.booth_id, v2.ward_id)), **dict(zip(v1.booth_id, v1.ward_id))}
        fc = pd.Series([f.scope.booth_id for f in self.flags]).value_counts().to_dict() if self.flags else {}
        dels = self.diff["deleted"]
        dup_records = {}
        for f in self.flags:
            if f.type == "duplicate_cluster":
                dup_records[f.scope.booth_id] = dup_records.get(f.scope.booth_id, 0) + len(f.scope.voter_ids)
        f_share = lambda df: df.assign(f=df.gender.eq("F")).groupby("booth_id").f.mean()  # noqa: E731
        fs1, fs2 = f_share(v1), f_share(v2)
        age_dist = {}
        for b, g in dels.groupby("booth_id"):
            ages = g.age.astype(int)
            age_dist[b] = {f"{lo}-{hi}": float(((ages >= lo) & (ages <= hi)).mean()) for lo, hi in BANDS}
        self.agg = {}
        for b in booths:
            r = t.loc[b]
            self.agg[b] = dict(
                n_v1=int(r.n_v1), n_v2=int(r.n_v2), deleted=int(r.del_obs), added=int(r.add_obs),
                del_exp=float(r.del_exp), add_exp=float(r.add_exp),
                del_q=float(r.del_q), add_q=float(r.add_q),
                del_rate=float(r.del_obs / r.n_v1) if r.n_v1 else 0.0,
                add_rate=float(r.add_obs / r.n_v2) if r.n_v2 else 0.0,
                dup_records=int(dup_records.get(b, 0)),
                f_share_v1=float(fs1.get(b, np.nan)), f_share_v2=float(fs2.get(b, np.nan)),
                age_dist=age_dist.get(b, {}), flag_count=int(fc.get(b, 0)))
        for metric in ("deleted", "added", "del_rate", "add_rate", "dup_records"):
            order = sorted(booths, key=lambda x: -self.agg[x][metric])
            for i, b in enumerate(order, 1):
                self.agg[b][f"rank_{metric}"] = i

    def overview(self) -> Overview:
        d = self.diff
        totals = Totals(v1=len(self.data.v1), v2=len(self.data.v2), added=len(d["added"]),
                        deleted=len(d["deleted"]), modified=len(d["modified"]))
        flagged = {}
        for f in self.flags:
            if f.type in ("deletion_spike", "addition_spike"):
                flagged.setdefault(f.scope.booth_id, set()).add(f.type)
        out = []
        for b in self.booths:
            a = self.agg[b]
            kinds = flagged.get(b, set())
            if "deletion_spike" in kinds and b in self.stories:
                outcome = self.stories[b].outcome
            elif kinds:
                outcome = "unusual"
            else:
                outcome = "normal"
            out.append(BoothSummary(booth_id=b, ward_id=self.ward.get(b, ""), n_v1=a["n_v1"], n_v2=a["n_v2"],
                                    del_rate=round(a["del_rate"], 5),
                                    expected_del_rate=round(a["del_exp"] / a["n_v1"], 5) if a["n_v1"] else 0.0,
                                    q_value=a["del_q"], flag_count=a["flag_count"], outcome=outcome))
        return Overview(totals=totals, booths=out)

    def toggle(self, booth: str, context_on: list[str]) -> StoryResult | None:
        key = tuple(sorted(set(context_on)))
        with self._lock:
            res = self._toggle_cache.get(key)
            if res is None:
                d = self.data
                res = compute_stories(d.v1, d.v2, d.death, d.hostel, d.boundary, self.clusters_v1, self.rates,
                                      context_on=list(key))
                self._toggle_cache[key] = res
        return res.get(booth)

    def rule_cards(self):
        """rules.json from engine/eval.py ({rules: [...]}) mapped onto RuleCard; context text from constants."""
        from api.constants import RULE_CONTEXT
        if not self.rules:
            return None
        rows = self.rules["rules"] if isinstance(self.rules, dict) else self.rules
        out = []
        for r in rows:
            if "rule_id" in r:
                out.append(RuleCard.model_validate(r))
                continue
            innocent, resolves = RULE_CONTEXT.get(r["rule"], ([], "A human review of the flagged records."))
            out.append(RuleCard(rule_id=r["rule"], what=r["definition"],
                                fires_on_benign_rate=r["false_positive_rate"],
                                innocent_explanations=innocent, resolves_with=resolves))
        return out

    def eval_result(self):
        return EvalResult.model_validate(self.eval) if self.eval else None


@lru_cache(maxsize=4)
def _store(d: str) -> Store:
    return Store(Path(d))


def store() -> Store:
    return _store(str(data_dir()))
