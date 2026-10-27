"""Cross-script duplicate detection (TRD 4.3). Character-n-gram style similarity, no embeddings."""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from itertools import combinations

import jellyfish
import pandas as pd
from indic_transliteration import sanscript
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

THRESHOLD = 0.88
_DEV = re.compile(r"[ऀ-ॿ]")


@lru_cache(maxsize=None)
def norm(s: str) -> str:
    s = s or ""
    if _DEV.search(s):
        s = sanscript.transliterate(s, sanscript.DEVANAGARI, sanscript.ITRANS)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z ]", "", s)
    for a, b in (("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"),
                 ("w", "v"), ("ph", "f"), ("sh", "s"), ("z", "j")):
        s = s.replace(a, b)
    toks = []
    for t in s.split():
        if len(t) > 2 and t.endswith("a"):
            t = t[:-1]  # final schwa
        toks.append(re.sub(r"(.)\1+", r"\1", t))
    return " ".join(toks)


def _best(a_lat, a_dev, b_lat, b_dev, fn) -> float:
    return max(fn(norm(a_lat), norm(b_lat)), fn(norm(a_dev), norm(b_dev)))


def pair_score(a, b) -> float:
    name = _best(a.name_lat, a.name_dev, b.name_lat, b.name_dev, JaroWinkler.similarity)
    rel = _best(a.relation_name_lat, a.relation_name_dev, b.relation_name_lat, b.relation_name_dev,
                lambda x, y: fuzz.token_set_ratio(x, y) / 100.0)
    ma, mb = jellyfish.metaphone(norm(a.name_lat)), jellyfish.metaphone(norm(b.name_lat))
    return 0.5 * name + 0.3 * rel + 0.2 * (1.0 if ma and ma == mb else 0.0)


def find_clusters(df: pd.DataFrame) -> list[dict]:
    """Clusters of >=2 records: {voter_ids, booth_id, house_no, score (weakest accepted link)}."""
    rows = {r.voter_id: r for r in df.itertuples()}
    blocks = defaultdict(list)
    for r in rows.values():
        blocks[("h", r.booth_id, r.house_no)].append(r.voter_id)
        blocks[("r", r.booth_id, norm(r.relation_name_lat)[:3])].append(r.voter_id)
    parent = {v: v for v in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    seen, edges = set(), {}
    for ids in blocks.values():
        for x, y in combinations(sorted(set(ids)), 2):
            if (x, y) in seen:
                continue
            seen.add((x, y))
            a, b = rows[x], rows[y]
            if a.gender != b.gender or abs(a.age - b.age) > 1:
                continue
            s = pair_score(a, b)
            if s >= THRESHOLD:
                edges[(x, y)] = s
                parent[find(x)] = find(y)
    groups = defaultdict(list)
    for v in rows:
        groups[find(v)].append(v)
    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        ms = sorted(members)
        sc = [s for (x, y), s in edges.items() if x in ms]
        first = rows[ms[0]]
        out.append({"voter_ids": ms, "booth_id": first.booth_id, "house_no": first.house_no, "score": float(min(sc))})
    return sorted(out, key=lambda c: c["voter_ids"])
