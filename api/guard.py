"""Neutrality Guard (TRD 6): structural -> lexicon -> rewrite (LLM if available) -> template fallback.

Every generated outbound string passes through `guard()`. Procedural text from api/constants.py is
allowlisted (stripped before matching). Every check is logged for /guard/log.
"""
from __future__ import annotations

import re
import threading
import time
from functools import lru_cache
from pathlib import Path

import yaml

from api import constants as C
from contracts.models import GuardLog, GuardLogItem, GuardResult

LEX_PATH = Path(__file__).with_name("guard_lexicon.yaml")
BLOCK_CATS = ("fraud", "party", "institution", "public_figure", "community", "real_place")
_W = r"0-9A-Za-z_ऀ-ॿ਀-੿"
_log: list[GuardLogItem] = []
_counts = {"checked": 0, "blocked": 0, "rewritten": 0}
_lock = threading.Lock()


@lru_cache(maxsize=1)
def lexicon() -> dict[str, list[str]]:
    raw = yaml.safe_load(LEX_PATH.read_text(encoding="utf-8")) or {}
    out = {}
    for cat, langs in raw.items():
        terms = []
        for v in (langs or {}).values():
            terms += [str(t) for t in v]
        out[cat] = terms
    return out


def _pattern(terms: list[str]) -> re.Pattern:
    alts = sorted({re.escape(t) for t in terms if t}, key=len, reverse=True)
    return re.compile(rf"(?<![{_W}])(?:{'|'.join(alts)})(?![{_W}])", re.IGNORECASE)


@lru_cache(maxsize=1)
def patterns() -> dict[str, re.Pattern]:
    lex = lexicon()
    pats = {c: _pattern(lex.get(c, [])) for c in BLOCK_CATS if lex.get(c)}
    try:  # synthetic person names from the generator's name list
        from generator.names import FEMALE, MALE
        names = [n for pair in MALE + FEMALE for n in pair]
        pats["person"] = _pattern(names)
    except Exception:
        pass
    return pats


@lru_cache(maxsize=1)
def allowlist() -> list[str]:
    """Every procedural string in constants.py (nested dicts flattened), longest first."""
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)

    for name in dir(C):
        if name.isupper() or name.startswith("_") and not name.startswith("__"):
            walk(getattr(C, name))
    return sorted({s for s in out if len(s) > 3}, key=len, reverse=True)


def find_terms(text: str, cats=None, allow_person: bool = False) -> list[str]:
    """Blocked terms found in text (after removing allowlisted procedural strings)."""
    t = text or ""
    for a in allowlist():
        if a in t:
            t = t.replace(a, " ")
    hits = []
    for cat, pat in patterns().items():
        if (cats and cat not in cats) or (cat == "person" and allow_person):
            continue
        hits += [m.group(0) for m in pat.finditer(t)]
    return list(dict.fromkeys(hits))


def _structural(text) -> list[str]:
    if not isinstance(text, str):
        return ["<non-text>"]
    if len(text) > 4000:
        return ["<too-long>"]
    return []


def _log_item(surface, terms, rewritten, fell_back):
    with _lock:
        _counts["checked"] += 1
        _counts["blocked"] += int(bool(terms))
        _counts["rewritten"] += int(rewritten)
        if terms or rewritten or fell_back or len(_log) < 200:
            _log.append(GuardLogItem(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), surface=surface, blocked_terms=terms,
                                     rewritten=rewritten, fell_back_to_template=fell_back))
            del _log[:-500]


def guard(text: str, surface: str = "claim", lang: str = "en", template: str | None = None,
          allow_person: bool = False) -> tuple[str, GuardResult]:
    """Return (safe_text, GuardResult). `template` is the neutral fallback (default: constants.GUARD_FALLBACK)."""
    terms = _structural(text) or find_terms(text, allow_person=allow_person)
    if not terms:
        _log_item(surface, [], False, False)
        return text, GuardResult(passed=True)
    rewritten = False
    if not _structural(text):
        from api import llm
        new = llm.rewrite_neutral(text, lang)
        if new and not find_terms(new, allow_person=allow_person):
            _log_item(surface, terms, True, False)
            return new, GuardResult(passed=True, blocked_terms=terms, rewritten=True)
        rewritten = bool(new)
    fb = template or C.GUARD_FALLBACK.get(lang, C.GUARD_FALLBACK["en"])
    _log_item(surface, terms, rewritten, True)
    return fb, GuardResult(passed=True, blocked_terms=terms, rewritten=rewritten)


def check(text: str, allow_person: bool = False, surface: str | None = None) -> GuardResult:
    """Pure check, no logging, no rewrite."""
    terms = _structural(text) or find_terms(text, allow_person=allow_person)
    return GuardResult(passed=not terms, blocked_terms=terms)


def log() -> GuardLog:
    with _lock:
        return GuardLog(checked=_counts["checked"], blocked=_counts["blocked"], rewritten=_counts["rewritten"],
                        items=list(reversed(_log[-100:])))
