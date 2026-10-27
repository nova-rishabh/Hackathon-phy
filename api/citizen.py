"""Citizen search + chat (TRD 7). Template path; LLM phrasing hook = phrase_with_llm.

Every number here (score, confidence) is computed in Python. The LLM hook may only rephrase text,
and falls back to the template when no key / no client / guard fails.
"""
import base64
import importlib
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter
from rapidfuzz import fuzz, process
from rapidfuzz.distance import JaroWinkler

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts.models import (CitizenAnswer, CitizenAsk, GuardResult, SearchMatch,  # noqa: E402
                              SearchResult)
from api import constants as C  # noqa: E402
from api.normalize import has_devanagari, has_gurmukhi, normalize  # noqa: E402

MATCH_MIN = 0.70
router = APIRouter()


# ------------------------------------------------------------------ data
def _data_dir() -> Path:
    env = os.environ.get("ROLLWATCH_DATA")
    if env:
        return Path(env)
    art = ROOT / "artifacts"
    return art if (art / "roll_v2.parquet").exists() or (art / "roll_v2.csv").exists() \
        else ROOT / "contracts" / "fixtures"


def _read(d: Path, stem: str, ctx: bool = False) -> pd.DataFrame:
    for base in ([d / "context", d] if ctx else [d]):
        for ext in (".parquet", ".csv"):
            p = base / (stem + ext)
            if p.exists():
                if ext == ".parquet":
                    return pd.read_parquet(p)
                return pd.read_csv(p, dtype=str, encoding="utf-8")
    return pd.DataFrame()


class Store:
    def __init__(self, d: Path):
        self.v1 = _read(d, "roll_v1").astype(str)
        self.v2 = _read(d, "roll_v2").astype(str)
        self.death = _read(d, "death_register", True).astype(str)
        self.hostel = _read(d, "hostel_list", True).astype(str)
        self.boundary = _read(d, "boundary_changes", True).astype(str)
        for df in (self.v1, self.v2):
            df["nk"] = df["name_lat"].map(normalize)
            df["nk_dev"] = df["name_dev"].map(normalize)
            df["rk"] = df["relation_name_lat"].map(normalize)
        self.r1 = self.v1.set_index("voter_id", drop=False)
        self.r2 = self.v2.set_index("voter_id", drop=False)
        old = self.v1[~self.v1.voter_id.isin(self.v2.voter_id)]
        self.cand = pd.concat([self.v2, old], ignore_index=True)
        # booth in v1 too, so "booth 47" also finds entries that moved out of 47
        self.cand["booth_v1"] = self.cand.voter_id.map(self.r1["booth_id"]).fillna("")
        self.cand["age_i"] = pd.to_numeric(self.cand["age"], errors="coerce")
        self._nk = self.cand.nk.tolist()
        self._nkd = self.cand.nk_dev.tolist()
        self._rk = self.cand.rk.tolist()
        # up to 3 name tokens per candidate (Latin key and Devanagari key) for per-token scoring
        self._tok = [[(k.split() + ["", "", ""])[j] for k in keys] for keys in (self._nk, self._nkd)
                     for j in range(3)]
        if len(self.death):
            self.death["nk"] = self.death["name_lat"].map(normalize)
        self._attr = None

    def attributor(self):
        """Per-voter story attribution, the same rules as engine/stories.py (built lazily)."""
        if self._attr is None:
            self._attr = _build_attributor(self) or False
        return self._attr or None


def _build_attributor(s: Store):
    try:
        from engine.dupes import find_clusters, norm
        from engine.stories import ALL_CONTEXT, _int, attribute
    except Exception:  # engine missing: local heuristic
        return None
    v1 = s.v1.copy()
    v1["age"] = pd.to_numeric(v1["age"], errors="coerce").fillna(-99).astype(int)
    try:
        clusters = find_clusters(v1)
    except Exception:
        clusters = []
    cl = {m: c["voter_ids"] for c in clusters for m in c["voter_ids"]}
    v2_booth = dict(zip(s.v2.voter_id, s.v2.booth_id))
    v2_ids = set(v2_booth)
    death_idx: dict = {}
    for r in s.death.itertuples():
        a = _int(r.age)
        if a is not None:
            death_idx.setdefault((r.booth_id, str(r.house_no)), []).append((norm(r.name_lat), a))
    host = {(r.booth_id, str(r.house_no)) for r in s.hostel.itertuples()}
    bnd = [(r.from_booth, r.to_booth, _int(r.house_from), _int(r.house_to))
           for r in s.boundary.itertuples()] if len(s.boundary) else []
    recs = v1.set_index("voter_id", drop=False)
    ctx = set(ALL_CONTEXT)

    def f(vid: str) -> str:
        return attribute(recs.loc[vid], v2_booth, v2_ids, cl, death_idx, host, bnd, ctx)
    return f


@lru_cache(maxsize=4)
def _store(d: str) -> Store:
    return Store(Path(d))


def store() -> Store:
    return _store(str(_data_dir()))


# ------------------------------------------------------------------ status / reason
_FIELDS = ["name_lat", "house_no", "booth_id", "age", "gender", "relation_name_lat"]
_STORY_TO_REASON = {"hostel_moveout": "shifted", "death_registered": "death_registered",
                    "duplicate_cleanup": "duplicate_cleanup", "boundary_change": "boundary_change",
                    "unexplained": "unexplained"}


def status_of(s: Store, vid: str) -> str:
    if vid not in s.r2.index:
        return "not_in_new_list"
    if vid not in s.r1.index:
        return "present"
    a, b = s.r1.loc[vid], s.r2.loc[vid]
    return "modified" if any(str(a[f]) != str(b[f]) for f in _FIELDS) else "present"


def reason_of(s: Store, vid: str, status: str) -> str:
    """Reason category for a changed entry, from the same story rules the engine uses."""
    if status not in ("modified", "not_in_new_list"):
        return "none"
    if status == "modified" and s.r1.loc[vid, "booth_id"] == s.r2.loc[vid, "booth_id"]:
        return "none"
    f = s.attributor()
    if f is not None:
        try:
            code = _STORY_TO_REASON.get(f(vid), "unexplained")
            if status == "modified" and code == "unexplained":
                return "none"  # moved booth but still on the roll
            return code
        except Exception:
            pass
    return _reason_fallback(s, vid, status)


def _reason_fallback(s: Store, vid: str, status: str) -> str:
    if status == "modified":
        return "boundary_change"
    r = s.r1.loc[vid]
    if len(s.death):
        d = s.death[(s.death.booth_id == r.booth_id) & (s.death.house_no == r.house_no)]
        if any(fuzz.ratio(r.nk, k) >= 80 for k in d.nk):
            return "death_registered"
    same = s.v2[(s.v2.booth_id == r.booth_id) & (s.v2.house_no == r.house_no)]
    if any(fuzz.ratio(r.nk, k) >= 85 for k in same.nk):
        return "duplicate_cleanup"
    if len(s.hostel) and len(s.hostel[(s.hostel.booth_id == r.booth_id)
                                      & (s.hostel.house_no == r.house_no)]):
        return "shifted"
    return "unexplained"


# ------------------------------------------------------------------ query parsing
_DIG = str.maketrans("०१२३४५६७८९੦੧੨੩੪੫੬੭੮੯", "01234567890123456789")
_BOOTH = re.compile(
    r"(?:\bboo?th\s*(?:no\.?|number|num|#)?\s*[:\-]?\s*|\bb\s*-?\s*"
    r"|बूथ\s*(?:नंबर|संख्या)?\s*[:\-]?\s*|ਬੂਥ\s*(?:ਨੰਬਰ)?\s*[:\-]?\s*)0*(\d{1,3})\b", re.I)
_AGE = re.compile(
    r"(?:\bage\s*[:\-]?\s*|\bumm?ar\s*|\bumr\s*|उम्र\s*|आयु\s*|ਉਮਰ\s*)(\d{2,3})\b"
    r"|\b(\d{2,3})\s*(?:years?|yrs?|y/o|saal|sal|baras|वर्ष|साल|ਸਾਲ)", re.I)
_REL = re.compile(r"\b(?:s/o|d/o|w/o|c/o|son of|daughter of|wife of|father|husband)\b|पुत्र|पुत्री|पत्नी|ਪੁੱਤਰ|ਧੀ",
                  re.I)
_SPLIT = re.compile(r"[\s,.?!।:;\-]+")


def _keep(s: str) -> list[str]:
    return [t for t in _SPLIT.split(s) if t and t.lower() not in C.STOPWORDS and not t.isdigit()]


def parse_query(q: str, booth_id: str | None = None, age: int | None = None):
    """-> (name_text, relation_text, booth_id|None, age|None)"""
    q = (q or "").translate(_DIG)
    m = _BOOTH.search(q)
    if m:
        booth_id = booth_id or f"B{int(m.group(1)):03d}"
        q = q[:m.start()] + " " + q[m.end():]
    m = _AGE.search(q)
    if m:
        age = age or int(m.group(1) or m.group(2))
        q = q[:m.start()] + " " + q[m.end():]
    rel = ""
    parts = _REL.split(q, maxsplit=1)
    if len(parts) == 2:
        q, rel = parts
    return " ".join(_keep(q)), " ".join(_keep(rel)), booth_id, age


# ------------------------------------------------------------------ search
def _sims(qn: str, keys: list[str]) -> np.ndarray:
    jw = process.cdist([qn], keys, scorer=JaroWinkler.normalized_similarity)[0]
    ts = process.cdist([qn], keys, scorer=fuzz.token_sort_ratio)[0] / 100.0
    return 0.5 * jw + 0.5 * ts


def _token_score(s: "Store", qn: str, idx: np.ndarray) -> np.ndarray:
    """Every query token must find a close name token: 0.5*mean + 0.5*min of per-token best ratio.
    Stops 'meena kumari' from matching 'meena kapoor' on the shared first name alone."""
    per = []
    for qt in qn.split()[:4]:
        best = np.zeros(len(idx))
        for col in s._tok:
            keys = [col[i] for i in idx]
            best = np.maximum(best, process.cdist([qt], keys, scorer=fuzz.ratio)[0] / 100.0)
        per.append(best)
    per = np.vstack(per)
    return 0.5 * per.mean(axis=0) + 0.5 * per.min(axis=0)


def search(q: str, booth_id: str | None = None, age: int | None = None, limit: int = 3) -> SearchResult:
    s = store()
    name, rel, booth, age = parse_query(q, booth_id, age)
    qn, qr = normalize(name), normalize(rel)
    if not qn or not len(s.cand):
        return SearchResult(matches=[], query_normalized=qn)
    mask = np.ones(len(s.cand), dtype=bool)
    if booth:
        mask &= ((s.cand.booth_id == booth) | (s.cand.booth_v1 == booth)).to_numpy()
    if age:
        near = ((s.cand.age_i - age).abs() <= 3).to_numpy()
        if (mask & near).any():
            mask &= near
    idx = np.flatnonzero(mask)
    if not len(idx):
        return SearchResult(matches=[], query_normalized=qn)
    sc = np.maximum(_sims(qn, [s._nk[i] for i in idx]), _sims(qn, [s._nkd[i] for i in idx]))
    sc = np.minimum(sc, _token_score(s, qn, idx))
    if qr:
        sc = 0.8 * sc + 0.2 * _sims(qr, [s._rk[i] for i in idx])
    out = []
    for o in np.argsort(-sc, kind="stable")[:limit]:
        r = s.cand.iloc[idx[o]]
        out.append(SearchMatch(voter_id=r.voter_id, name_dev=r.name_dev, name_lat=r.name_lat,
                               booth_id=r.booth_id, status_v2=status_of(s, r.voter_id),
                               score=round(float(min(sc[o], 1.0)), 3)))
    return SearchResult(matches=out, query_normalized=qn)


# ------------------------------------------------------------------ language
_HINGLISH = set("""mera meri mere naam nam hai hain kya kyu kyun mein hun hu hoon nahi nahin
kaise kahan kab kaun aap apna apni batao bataiye dekho dekhiye suchi se ko ka ki ke tha thi
kaat diye kat gaya hata hataya kripya ji bhai""".split())
_ENGLISH = set("is my name the in list please check what why how where am i".split())


def detect_lang(text: str, req_lang: str | None = None) -> str:
    """Script first (Devanagari -> hi, Gurmukhi -> pa). Latin: Hinglish markers -> hi, else en."""
    if has_devanagari(text):
        return "hi"
    if has_gurmukhi(text):
        return "pa"
    if req_lang:
        return req_lang
    toks = [t.lower() for t in _SPLIT.split(text or "") if t]
    hi = sum(t in _HINGLISH for t in toks)
    en = sum(t in _ENGLISH for t in toks)
    return "hi" if hi >= 2 and hi > en else "en"


# ------------------------------------------------------------------ LLM hook
def phrase_with_llm(text: str, lang: str) -> tuple[str, GuardResult]:
    """Optional LLM rephrase of the templated text, through the guard.

    Falls back to the template when there is no key, DEMO_MODE=1, api.llm / api.guard are missing,
    or anything fails. A rephrase whose digits differ from the template is rejected.
    Expected (A1): api.llm.phrase(text, lang=, surface=) -> str; api.guard.check(text, surface=) -> GuardResult.
    """
    ok = GuardResult(passed=True)
    if os.environ.get("DEMO_MODE") == "1" or not os.environ.get("ANTHROPIC_API_KEY"):
        return text, ok
    try:
        llm = importlib.import_module("api.llm")
        guard = importlib.import_module("api.guard")
        new = llm.phrase(text, lang=lang, surface="citizen")
        if not new or sorted(re.findall(r"\d+", new)) != sorted(re.findall(r"\d+", text)):
            return text, ok
        g = guard.check(new, surface="citizen")
        g = g if isinstance(g, GuardResult) else GuardResult(**dict(g))
        if g.passed:
            return new, g
        return text, GuardResult(passed=True, blocked_terms=g.blocked_terms, rewritten=True)
    except Exception:
        return text, ok


# ------------------------------------------------------------------ ask
def _answer(lang, status, reason, steps, conf, match, lines, transcript=None):
    text, guard = phrase_with_llm("\n".join(lines), lang)
    return CitizenAnswer(lang=lang, transcript=transcript, answer_text=text, match=match,
                         status=status, reason_category=reason, next_steps=steps,
                         confidence=round(float(max(0.0, min(conf, 1.0))), 3), guard=guard)


def _shown_name(match: SearchMatch, lang: str) -> str:
    if lang in ("hi", "pa"):
        return match.name_dev or match.name_lat
    return f"{match.name_lat} / {match.name_dev}" if match.name_dev else match.name_lat


def _transcribe(audio_b64: str) -> str:
    """Web audio path (S3). Needs SARVAM_API_KEY; returns '' when unavailable."""
    if not os.environ.get("SARVAM_API_KEY"):
        return ""
    try:
        from bot import sarvam
        return sarvam.stt_any(base64.b64decode(audio_b64)) or ""
    except Exception:
        return ""


def ask(req: CitizenAsk) -> CitizenAnswer:
    text = (req.text or "").strip()
    transcript = None
    if req.audio_b64 and not text:
        transcript = _transcribe(req.audio_b64) or None
        text = transcript or ""
        if not text:
            lang = req.lang or "hi"
            return _answer(lang, "not_found", "none", [], 0.0, None,
                           [C.VOICE_SOON[lang], C.PORTAL_LINE[lang], C.SCAM_LINE[lang]])
    lang = detect_lang(text, req.lang)
    footer = [C.PORTAL_LINE[lang], C.SCAM_LINE[lang]]
    name, _, _, _ = parse_query(text)
    if not normalize(name):
        return _answer(lang, "not_found", "none", [], 0.0, None, [C.NO_QUERY[lang]] + footer, transcript)
    res = search(text, limit=1)
    best = res.matches[0] if res.matches else None
    if not best or best.score < MATCH_MIN:
        status, reason, match = "not_found", "none", None
        conf = float(best.score) if best else 0.0
    else:
        status, match, conf = best.status_v2, best, best.score
        reason = reason_of(store(), best.voter_id, status)
    key = reason if reason in C.NEXT_STEPS[status] else None
    steps = [st[lang] for st in C.NEXT_STEPS[status][key]]
    lines = []
    if match:
        lines.append(C.STATUS_LINE[status][lang].format(name=_shown_name(match, lang), booth=match.booth_id))
        if reason in C.REASON_LINE:
            lines.append(C.REASON_LINE[reason][lang])
        lines.append(C.LABELS["sure"][lang].format(pct=round(conf * 100)))
    else:
        lines.append(C.STATUS_LINE["not_found"][lang])
        lines.append(C.LABELS["sure_none"][lang])
    lines.append(C.LABELS["next"][lang])
    lines += [f"{i}. {t}" for i, t in enumerate(steps, 1)]
    if status != "present":
        lines.append(C.DEADLINE_LINE[lang])
    return _answer(lang, status, reason, steps, conf, match, lines + footer, transcript)


# ------------------------------------------------------------------ router
@router.get("/search", response_model=SearchResult)
def get_search(q: str, booth_id: str | None = None, age: int | None = None):
    return search(q, booth_id, age)


@router.post("/citizen/ask", response_model=CitizenAnswer)
def post_ask(req: CitizenAsk):
    return ask(req)
