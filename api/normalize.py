"""Indian-name normaliser (TRD 4.3). Pure functions."""
import re
import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

_DEV = re.compile(r"[\u0900-\u097F]")
_GUR = re.compile(r"[\u0A00-\u0A7F]")


def has_devanagari(s: str) -> bool:
    return bool(_DEV.search(s or ""))


def has_gurmukhi(s: str) -> bool:
    return bool(_GUR.search(s or ""))


def to_itrans(s: str) -> str:
    if has_devanagari(s):
        s = transliterate(s, sanscript.DEVANAGARI, sanscript.ITRANS)
    elif has_gurmukhi(s):
        s = transliterate(s, sanscript.GURMUKHI, sanscript.ITRANS)
    return s


def _strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_token(t: str) -> str:
    t = t.lower()
    for a, b in (("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"),
                 ("w", "v"), ("ph", "f"), ("sh", "s"), ("z", "j")):
        t = t.replace(a, b)
    if len(t) > 2 and t.endswith("a"):
        t = t[:-1]
    return re.sub(r"(.)\1+", r"\1", t)


def normalize(name: str) -> str:
    """Devanagari/Gurmukhi/Latin name -> comparable ASCII key."""
    s = _strip_diacritics(to_itrans(name or "")).lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    return " ".join(normalize_token(t) for t in s.split())
