"""Citizen search + chat (template path; LLM phrasing hook = phrase_with_llm)."""
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter
from rapidfuzz import fuzz
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
    return art if (art / "roll_v2.parquet").exists() else ROOT / "contracts" / "fixtures"


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
        for df in (self.v1, self.v2):
            df["nk"] = df["name_lat"].map(normalize)
            df["nk_dev"] = df["name_dev"].map(normalize)
            df["rk"] = df["relation_name_lat"].map(normalize)
        self.r1 = self.v1.set_index("voter_id", drop=False)
        self.r2 = self.v2.set_index("voter_id", drop=False)
        self.cand = pd.concat([self.v2, self.v1[~self.v1.voter_id.isin(self.v2.voter_id)]],
                              ignore_index=True)
        if len(self.death):
            self.death["nk"] = self.death["name_lat"].map(normalize)


@lru_cache(maxsize=4)
def _store(d: str) -> Store:
    return Store(Path(d))


def store() -> Store:
    return _store(str(_data_dir()))


# ------------------------------------------------------------------ status / reason
_FIELDS = ["name_lat", "house_no", "booth_id", "age", "gender", "relation_name_lat"]


def status_of(s: Store, vid: str) -> str:
    if vid not in s.r2.index:
        return "not_in_new_list"
    if vid not in s.r1.index:
        return "present"
    a, b = s.r1.loc[vid], s.r2.loc[vid]
    return "modified" if any(str(a[f]) != str(b[f]) for f in _FIELDS) else "present"


def reason_of(s: Store, vid: str, status: str) -> str:
    if status == "present":
        return "none"
    if status == "modified":
        a, b = s.r1.loc[vid], s.r2.loc[vid]
        return "boundary_change" if a["booth_id"] != b["booth_id"] else "none"
    if status != "not_in_new_list":
        return "none"
    r = s.r1.loc[vid]
    if len(s.death):
        d = s.death[(s.death.booth_id == r.booth_id) & (s.death.house_no == r.house_no)]
        if any(fuzz.ratio(r.nk, k) >= 80 for k in d.nk):
            return "death_registered"
    same = s.v2[(s.v2.booth_id == r.booth_id) & (s.v2.house_no == r.house_no)]
    if any(fuzz.ratio(r.nk, k) >= 85 for k in same.nk):
        return "duplicate_cleanup"
    other = s.v2[(s.v2.booth_id != r.booth_id) & (s.v2.nk == r.nk) & (s.v2.house_no == r.house_no)]
    if len(other):
        return "boundary_change"
    if len(s.hostel) and len(s.hostel[(s.hostel.booth_id == r.booth_id)
                                      & (s.hostel.house_no == r.house_no)]):
        return "shifted"
    return "unexplained"


# ------------------------------------------------------------------ search
_BOOTH = re.compile(
    r"(?:booth\s*(?:no\.?|number|#)?\s*[:\-]?\s*|\bb\s*|बूथ\s*(?:नंबर|संख्या)?\s*|ਬੂਥ\s*(?:ਨੰਬਰ)?\s*)(\d{1,3})\b",
    re.I)
_REL = re.compile(r"\b(?:s/o|d/o|w/o|son of|daughter of|wife of|father|husband)\b|पुत्र|पुत्री|पत्नी|ਪੁੱਤਰ|ਧੀ",
                  re.I)


def parse_query(q: str, booth_id: str | None = None):
    """-> (name_text, relation_text, booth_id|None)"""
    q = q or ""
    m = _BOOTH.search(q)
    if m:
        booth_id = booth_id or f"B{int(m.group(1)):03d}"
        q = q[:m.start()] + " " + q[m.end():]
    rel = ""
    parts = _REL.split(q, maxsplit=1)
    if len(parts) == 2:
        q, rel = parts
    toks = [t for t in re.split(r"[\s,.?!।]+", q) if t and t.lower() not in C.STOPWORDS]
    rtoks = [t for t in re.split(r"[\s,.?!।]+", rel) if t and t.lower() not in C.STOPWORDS]
    return " ".join(toks), " ".join(rtoks), booth_id


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return 0.5 * JaroWinkler.similarity(a, b) + 0.5 * fuzz.token_sort_ratio(a, b) / 100


def search(q: str, booth_id: str | None = None) -> SearchResult:
    s = store()
    name, rel, booth = parse_query(q, booth_id)
    qn, qr = normalize(name), normalize(rel)
    df = s.cand
    if booth:
        def in_booth(v):
            return booth in (s.r1.loc[v].booth_id if v in s.r1.index else None,
                             s.r2.loc[v].booth_id if v in s.r2.index else None)
        df = df[df.voter_id.map(in_booth)]
    scored = []
    for r in df.itertuples():
        sc = max(_sim(qn, r.nk), _sim(qn, r.nk_dev))
        if qr:
            sc = 0.8 * sc + 0.2 * _sim(qr, r.rk)
        scored.append((sc, r))
    scored.sort(key=lambda x: -x[0])
    out = [SearchMatch(voter_id=r.voter_id, name_dev=r.name_dev, name_lat=r.name_lat,
                       booth_id=r.booth_id, status_v2=status_of(s, r.voter_id),
                       score=round(float(sc), 3))
           for sc, r in scored[:3]]
    return SearchResult(matches=out, query_normalized=qn)


# ------------------------------------------------------------------ ask
def detect_lang(text: str, req_lang: str | None) -> str:
    if has_devanagari(text):
        return "hi"
    if has_gurmukhi(text):
        return "pa"
    return req_lang or "en"


def phrase_with_llm(text: str, lang: str) -> str:
    """Hook: later rephrase the templated text via the LLM + guard. Identity for now."""
    return text


def _answer(lang, status, reason, steps, conf, match, lines):
    return CitizenAnswer(lang=lang, answer_text=phrase_with_llm("\n".join(lines), lang),
                         match=match, status=status, reason_category=reason, next_steps=steps,
                         confidence=conf, guard=GuardResult(passed=True))


def ask(req: CitizenAsk) -> CitizenAnswer:
    text = (req.text or "").strip()
    lang = detect_lang(text, req.lang)
    footer = [C.PORTAL_LINE[lang], C.SCAM_LINE[lang]]
    if req.audio_b64 and not text:
        return _answer(lang, "not_found", "none", [], 0.0, None, [C.VOICE_SOON[lang]] + footer)
    name, _, _ = parse_query(text, None)
    if not normalize(name):
        return _answer(lang, "not_found", "none", [], 0.0, None, [C.NO_QUERY[lang]] + footer)
    res = search(text)
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
        shown = match.name_dev if lang == "hi" else match.name_lat
        lines.append(C.STATUS_LINE[status][lang].format(name=shown, booth=match.booth_id))
        if reason in C.REASON_LINE:
            lines.append(C.REASON_LINE[reason][lang])
        lines.append(C.LABELS["sure"][lang].format(pct=round(conf * 100)))
    else:
        lines.append(C.STATUS_LINE["not_found"][lang])
        lines.append(C.LABELS["sure_none"][lang])
    lines.append(C.LABELS["next"][lang])
    lines += [f"{i}. {t}" for i, t in enumerate(steps, 1)]
    return _answer(lang, status, reason, steps, conf, match, lines + footer)


# ------------------------------------------------------------------ router
@router.get("/search", response_model=SearchResult)
def get_search(q: str, booth_id: str | None = None):
    return search(q, booth_id)


@router.post("/citizen/ask", response_model=CitizenAnswer)
def post_ask(req: CitizenAsk):
    return ask(req)
