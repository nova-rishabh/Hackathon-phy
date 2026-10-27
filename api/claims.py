"""Claim Court (TRD 5): placeholders -> split (LLM tool call, else rule-based) -> hard rules in code ->
tools over precomputed aggregates (O(1)) -> deterministic verdict -> mirror. The agent plans, code decides."""
from __future__ import annotations

import hashlib
import re

from api import constants as C
from api import llm
from api.guard import find_terms, guard, patterns
from api.store import store
from contracts.models import (ClaimCheckRequest, ClaimInput, ClaimVerdict, Evidence, EvidencePoint, GuardResult,
                              Mirror, SubClaim)

TOOLS = ["deletion_count", "deletion_rate", "addition_count", "duplicate_count", "age_distribution",
         "gender_ratio", "compare_booths", "story_shares", "unanswerable"]

# ------------------------------------------------------------------ hard-rule vocabularies (code, not prompt)
INTENT = ["targeted", "targeting", "deliberately", "deliberate", "on purpose", "intentionally", "rigged", "rigging",
          "conspiracy", "plot", "fraud", "scam", "stolen", "chori", "saazish", "sajish", "jaanbujhkar", "jaan bujhkar",
          "साजिश", "साज़िश", "जानबूझकर", "जान बूझकर", "षड्यंत्र", "धांधली", "चोरी", "ਸਾਜ਼ਿਸ਼", "ਜਾਣਬੁੱਝ ਕੇ", "ਧਾਂਦਲੀ", "ਚੋਰੀ"]
EXISTENCE = ["ghost", "ghosts", "fake", "bogus", "farzi", "farji", "फर्जी", "फ़र्जी", "भूत", "ਜਾਅਲੀ", "ਫ਼ਰਜ਼ੀ", "non-existent"]
DEL_WORDS = ["kaat", "kaate", "kat", "kate", "cut", "removed", "remove", "deleted", "delete", "deletion", "deletions",
             "hataye", "hata", "hatae", "dropped", "struck", "missing", "gayab", "कट", "काट", "हटा", "हटाए", "डिलीट",
             "ग़ायब", "गायब", "ਕੱਟ", "ਹਟਾ", "ਹਟਾਏ"]
ADD_WORDS = ["added", "add", "addition", "additions", "jode", "jod", "jude", "joda", "inserted", "new names", "enrolled",
             "जोड़", "जोड़े", "जुड़े", "ਜੋੜ", "ਜੋੜੇ"]
MOST_WORDS = ["sabse zyada", "sabse jyada", "sabse zyaada", "most", "highest", "maximum", "largest", "the most",
              "सबसे ज़्यादा", "सबसे ज्यादा", "सर्वाधिक", "ਸਭ ਤੋਂ ਵੱਧ", "ਸਭ ਤੋਂ ਜ਼ਿਆਦਾ"]
DUP_WORDS = ["duplicate", "duplicates", "double", "twice", "dohra", "दोहरे", "डुप्लीकेट", "ਦੋਹਰੇ"]
RATE_WORDS = ["%", "percent", "per cent", "pratishat", "प्रतिशत", "ਪ੍ਰਤੀਸ਼ਤ"]
WOMEN_WORDS = ["women", "woman", "female", "mahila", "mahilayen", "aurat", "auraten", "महिला", "महिलाएं", "औरत", "ਔਰਤ", "ਔਰਤਾਂ"]
OLD_WORDS = ["elderly", "old people", "senior", "buzurg", "बुजुर्ग", "बुज़ुर्ग", "ਬਜ਼ੁਰਗ"]
YOUNG_WORDS = ["young", "youth", "students", "yuva", "युवा", "छात्र", "ਨੌਜਵਾਨ"]
MANY_WORDS = ["many", "lots", "bahut", "hazaron", "sainkdon", "बहुत", "हज़ारों", "सैकड़ों", "ਬਹੁਤ"]
HINGLISH = ["mein", "naam", "kaat", "diye", "sabse", "zyada", "aur", "ke", "ki", "hai", "jode", "gaye"]

_W = r"0-9A-Za-z_ऀ-ॿ਀-੿"
BOOTH_RE = re.compile(r"(?:booth|boot|बूथ|ਬੂਥ|part|भाग)\s*(?:no\.?|number|नंबर|ਨੰਬਰ)?\s*#?\s*(\d{1,3})|\bB(\d{3})\b", re.I)
NUM_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|percent|per cent|प्रतिशत)?", re.I)
SPLIT_RE = re.compile(r"\s*(?:[,;।!?]|\.(?!\d)|\band\b|\baur\b|\bor\b|\bbut\b|\bलेकिन\b|\bऔर\b|\bਅਤੇ\b|\bਤੇ\b)\s*", re.I)


def _has(text: str, words: list[str]) -> bool:
    t = text.lower()
    for w in words:
        if re.search(rf"(?<![{_W}]){re.escape(w.lower())}", t):
            return True
    return False


def detect_lang(text: str) -> str:
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    if re.search(r"[਀-੿]", text):
        return "pa"
    words = set(re.findall(r"[a-z]+", text.lower()))
    return "hi" if len(words & set(HINGLISH)) >= 2 else "en"


def placeholders(text: str) -> str:
    """Party and person names -> [GROUP A]/[GROUP B]/[PERSON] before anything else runs."""
    pats = patterns()
    groups: dict[str, str] = {}

    def grp(m):
        k = m.group(0).lower()
        if k not in groups:
            groups[k] = f"[GROUP {chr(65 + len(groups))}]"
        return groups[k]

    out = pats["party"].sub(grp, text) if "party" in pats else text
    for cat in ("public_figure", "person"):
        if cat in pats:
            out = pats[cat].sub("[PERSON]", out)
    return out


def _booth(n) -> str | None:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return None
    b = f"B{n:03d}"
    return b if b in store().agg else None


# ------------------------------------------------------------------ rule-based splitter (no keys / fallback)
def rule_split(text: str) -> list[dict]:
    clauses = [c for c in SPLIT_RE.split(text) if c and c.strip()]
    subs, booth, direction = [], None, None
    for c in clauses:
        cl = c.strip()
        bm = BOOTH_RE.search(cl)
        if bm:
            booth = _booth(bm.group(1) or bm.group(2)) or f"B{int(bm.group(1) or bm.group(2)):03d}"
        rest = BOOTH_RE.sub(" ", cl)
        nums = [(float(m.group(1).replace(",", "")), bool(m.group(2))) for m in NUM_RE.finditer(rest)]
        is_rate = any(p for _, p in nums) or _has(cl, RATE_WORDS)
        if _has(cl, DEL_WORDS):
            direction = "del"
        elif _has(cl, ADD_WORDS):
            direction = "add"
        base = {"text": cl, "params": {"booth_id": booth} if booth else {}, "claimed_value": None}
        if find_terms(cl, cats=("community",)) or _has(cl, INTENT) or find_terms(cl, cats=("real_place",)):
            subs.append({**base, "tool": "unanswerable"})
            continue
        if _has(cl, EXISTENCE):
            # "ghost voters added": the count is checkable, whether people exist is not.
            if direction:
                subs.append({**base, "tool": "addition_count" if direction == "add" else "deletion_count",
                             "params": {**base["params"], "mode": "above_expected"}, "claimed_value": 1.0,
                             "text": cl + " (more than expected)"})
            subs.append({**base, "tool": "unanswerable", "text": cl + " (the people do not exist)", "existence": True})
            continue
        if _has(cl, MOST_WORDS):
            subs.append({**base, "tool": "compare_booths",
                         "params": {**base["params"], "metric": "added" if direction == "add" else "deleted"},
                         "claimed_value": 1.0})
            continue
        if _has(cl, DUP_WORDS):
            subs.append({**base, "tool": "duplicate_count", "claimed_value": nums[0][0] if nums else None})
            continue
        if _has(cl, WOMEN_WORDS) and is_rate:
            subs.append({**base, "tool": "gender_ratio", "claimed_value": nums[0][0] if nums else None})
            continue
        if (_has(cl, OLD_WORDS) or _has(cl, YOUNG_WORDS)) and direction == "del":
            band = "75-200" if _has(cl, OLD_WORDS) else "0-24"
            subs.append({**base, "tool": "age_distribution", "params": {**base["params"], "band": band},
                         "claimed_value": nums[0][0] if nums and is_rate else None})
            continue
        if direction and nums:
            tool = ("deletion_rate" if direction == "del" else "addition_count") if is_rate else \
                   ("deletion_count" if direction == "del" else "addition_count")
            if is_rate and direction == "add":
                tool = "addition_count"
                base["params"]["as_rate"] = 1
            subs.append({**base, "tool": tool, "claimed_value": nums[0][0]})
            continue
        if direction and (_has(cl, MANY_WORDS) or bm):
            subs.append({**base, "tool": "addition_count" if direction == "add" else "deletion_count",
                         "params": {**base["params"], "mode": "above_expected"}, "claimed_value": 1.0,
                         "text": cl + " (more than expected)"})
            continue
        if len(re.findall(rf"[{_W}]+", cl)) >= 2:
            subs.append({**base, "tool": "unanswerable", "unknown": True})
    return subs


SPLIT_TOOL = {
    "name": "split_claim",
    "description": "Split a forwarded claim about the voter roll into atomic, checkable sub-claims.",
    "input_schema": {"type": "object", "required": ["sub_claims"], "properties": {"sub_claims": {
        "type": "array", "items": {"type": "object", "required": ["text", "tool"], "properties": {
            "text": {"type": "string", "description": "Neutral English restatement of this part."},
            "tool": {"type": "string", "enum": TOOLS},
            "params": {"type": "object", "properties": {
                "booth_id": {"type": "string", "description": "B001..B100"},
                "metric": {"type": "string", "enum": ["deleted", "added", "del_rate", "dup_records"]},
                "band": {"type": "string"}, "code": {"type": "string"},
                "mode": {"type": "string", "enum": ["above_expected"]}}},
            "claimed_value": {"type": ["number", "null"]}}}}}},
}
SPLIT_SYSTEM = ("You split forwarded claims about a voter roll into sub-claims. Pick each tool only from the menu. "
                "Never compute numbers; copy the number the claim states into claimed_value (null if none). "
                "For 'the most of any booth' use compare_booths with claimed_value 1. Religion, caste, community, "
                "motive or real places -> unanswerable. Booth ids look like B047.")


def split(text: str) -> tuple[list[dict], str]:
    out = llm.call(C.MODEL_SPLIT, SPLIT_SYSTEM, text, SPLIT_TOOL)
    subs = out.get("sub_claims") if isinstance(out, dict) else None
    if isinstance(subs, list) and subs:
        clean = []
        for s in subs:
            if not isinstance(s, dict) or s.get("tool") not in TOOLS:
                continue
            p = {k: v for k, v in (s.get("params") or {}).items() if isinstance(v, (str, int, float))}
            if "booth_id" in p:
                m = re.search(r"(\d{1,3})", str(p["booth_id"]))
                p["booth_id"] = _booth(m.group(1)) if m else None
                if not p["booth_id"]:
                    p.pop("booth_id")
            cv = s.get("claimed_value")
            clean.append({"text": str(s.get("text", ""))[:300], "tool": s["tool"], "params": p,
                          "claimed_value": float(cv) if isinstance(cv, (int, float)) else None})
        if clean:
            return clean, "llm"
    return rule_split(text), "rules"


# ------------------------------------------------------------------ hard rules (after the split)
def hard_rule(sub: dict, original: str) -> tuple[str, str] | None:
    t = sub["text"]
    if find_terms(t, cats=("community",)) or (sub["tool"] == "unanswerable" and find_terms(original, cats=("community",))
                                              and not sub.get("existence") and not _has(t, INTENT)):
        return C.REASON_COMMUNITY, C.SETTLE_COMMUNITY
    if _has(t, INTENT):
        return C.REASON_MOTIVE, C.SETTLE_MOTIVE
    if find_terms(t, cats=("real_place",)):
        return C.REASON_PLACE, C.SETTLE_DEFAULT
    return None


# ------------------------------------------------------------------ tools (O(1) over precomputed aggregates)
def run_tool(tool: str, params: dict) -> tuple[float | None, str, Evidence, int]:
    s = store()
    b = params.get("booth_id")
    a = s.agg.get(b) if b else None
    if tool == "unanswerable":
        return None, "no query: this part cannot be measured from roll data", Evidence(), 0
    if tool in ("deletion_count", "deletion_rate", "addition_count", "duplicate_count", "age_distribution",
                "gender_ratio", "story_shares", "compare_booths") and a is None:
        return None, f"booth {b or '(none given)'} not found in the roll", Evidence(), 0
    if tool == "deletion_count":
        ev = Evidence(series=[EvidencePoint(label="removed", value=a["deleted"]),
                              EvidencePoint(label="expected", value=round(a["del_exp"], 1))],
                      note=f"q-value {a['del_q']:.2g} against the age-adjusted expectation")
        if params.get("mode") == "above_expected":
            return (1.0 if a["del_q"] < 0.05 else 0.0,
                    f"count v1 records where booth={b} and voter_id not in v2; test vs expected (BH q<0.05)", ev, a["n_v1"])
        return float(a["deleted"]), f"count v1 records where booth={b} and voter_id not in v2", ev, a["n_v1"]
    if tool == "deletion_rate":
        return (round(a["del_rate"] * 100, 2), f"removed / v1 records where booth={b}, as %",
                Evidence(series=[EvidencePoint(label="rate %", value=round(a["del_rate"] * 100, 2)),
                                 EvidencePoint(label="expected %", value=round(a["del_exp"] / max(a["n_v1"], 1) * 100, 2))]),
                a["n_v1"])
    if tool == "addition_count":
        ev = Evidence(series=[EvidencePoint(label="added", value=a["added"]),
                              EvidencePoint(label="expected", value=round(a["add_exp"], 1))],
                      note=f"q-value {a['add_q']:.2g} against the district addition rate")
        if params.get("mode") == "above_expected":
            return (1.0 if a["add_q"] < 0.05 else 0.0,
                    f"count v2 records where booth={b} and voter_id not in v1; test vs expected (BH q<0.05)", ev, a["n_v2"])
        if params.get("as_rate"):
            return round(a["add_rate"] * 100, 2), f"added / v2 records where booth={b}, as %", ev, a["n_v2"]
        return float(a["added"]), f"count v2 records where booth={b} and voter_id not in v1", ev, a["n_v2"]
    if tool == "duplicate_count":
        return (float(a["dup_records"]), f"count records in duplicate clusters where booth={b}",
                Evidence(series=[EvidencePoint(label="in duplicate clusters", value=a["dup_records"])]), a["n_v1"])
    if tool == "gender_ratio":
        v = round(a["f_share_v2"] * 100, 2)
        return (v, f"share of F records in v2 where booth={b}, as %",
                Evidence(series=[EvidencePoint(label="F % v1", value=round(a["f_share_v1"] * 100, 2)),
                                 EvidencePoint(label="F % v2", value=v)]), a["n_v2"])
    if tool == "age_distribution":
        band = str(params.get("band", "75-200"))
        dist = a["age_dist"]
        v = round(dist.get(band, 0.0) * 100, 2)
        return (v, f"share of removed records aged {band} where booth={b}, as %",
                Evidence(series=[EvidencePoint(label=k, value=round(x * 100, 2)) for k, x in dist.items()]), a["deleted"])
    if tool == "story_shares":
        st = s.stories.get(b)
        code = str(params.get("code", "unexplained"))
        if not st:
            return None, f"no removals in booth={b}", Evidence(), 0
        sh = next((x.share for x in st.stories if x.code == code), 0.0)
        return (round(sh * 100, 2), f"share of removals attributed to '{code}' where booth={b}, as %",
                Evidence(series=[EvidencePoint(label=x.code, value=round(x.share * 100, 2)) for x in st.stories]),
                st.removed_total)
    if tool == "compare_booths":
        metric = str(params.get("metric", "deleted"))
        if metric not in ("deleted", "added", "del_rate", "add_rate", "dup_records"):
            metric = "deleted"
        top = sorted(s.agg, key=lambda x: -s.agg[x][metric])[:5]
        return (float(a[f"rank_{metric}"]), f"rank of booth={b} by {metric} among {len(s.agg)} booths (1 = most)",
                Evidence(series=[EvidencePoint(label=x, value=round(s.agg[x][metric], 4)) for x in top],
                         note="top 5 booths"), len(s.agg))
    return None, "unknown tool", Evidence(), 0


def verdict_of(claimed: float | None, computed: float | None, tol: float = C.CLAIM_TOLERANCE,
               unanswerable: bool = False) -> tuple[str, float]:
    """Deterministic rule. Returns (verdict, relative error or nan)."""
    if unanswerable or claimed is None or computed is None:
        return "unprovable", float("nan")
    denom = max(abs(computed), 1e-9)
    rel = abs(claimed - computed) / denom
    return ("verified" if rel <= tol else "disputed"), rel


def _confidence(verdict: str, rel: float, n: int, tol: float) -> float:
    if verdict == "unprovable":
        return 0.9
    margin = min(1.0, abs(rel - tol) / tol)
    size = min(1.0, n / 200) if n else 0.5
    return round(0.5 + 0.45 * margin * (0.6 + 0.4 * size), 3)


def _reason(verdict, tool, claimed, computed, rel, params) -> str:
    if params.get("mode") == "above_expected":
        return ("The count is significantly above the age-adjusted expectation (BH q<0.05)." if verdict == "verified"
                else "The count is within what the expectation allows (BH q≥0.05).")
    if tool == "compare_booths":
        return (f"Rank {int(computed)} of {len(store().agg)} booths." if computed is not None else C.REASON_UNKNOWN)
    if verdict == "verified":
        return f"Computed {computed:g} vs claimed {claimed:g}: within the {round(C.CLAIM_TOLERANCE * 100)}% tolerance."
    if verdict == "disputed":
        return f"Computed {computed:g} vs claimed {claimed:g}: {round(rel * 100)}% off, outside the {round(C.CLAIM_TOLERANCE * 100)}% tolerance."
    return C.REASON_NO_NUMBER if claimed is None else C.REASON_UNKNOWN


def execute(subs: list[dict], original: str, prefix: str = "s") -> list[SubClaim]:
    out = []
    for i, s in enumerate(subs, 1):
        hr = hard_rule(s, original)
        tool = "unanswerable" if hr else s["tool"]
        params = dict(s.get("params") or {})
        if hr or tool == "unanswerable":
            if not hr:
                hr = ((C.REASON_UNKNOWN if s.get("unknown") else
                       "Whether these people exist can't be proven from roll data; field verification settles it.")
                      if not s.get("existence") else
                      ("Whether these people exist can't be proven from roll data; field verification settles it.", None))
                hr = hr if isinstance(hr, tuple) else (hr, None)
            reason, settle = hr
            settle = settle or ("Physical verification by the BLO (house visit)." if s.get("existence") else C.SETTLE_DEFAULT)
            text, _ = guard(s["text"], "claim", "en", template="[part of the claim withheld by the neutrality check]")
            out.append(SubClaim(id=f"{prefix}{i}", text=text, tool="unanswerable", params=params,
                                query_shown="no query: " + reason.rstrip("."), claimed_value=s.get("claimed_value"),
                                computed_value=None, verdict="unprovable", reason=reason, confidence=0.9,
                                settle_with=settle))
            continue
        computed, query, ev, n = run_tool(tool, params)
        claimed = s.get("claimed_value")
        v, rel = verdict_of(claimed, computed)
        text, _ = guard(s["text"], "claim", "en", template=f"Sub-claim checked with {tool}.")
        out.append(SubClaim(id=f"{prefix}{i}", text=text, tool=tool, params=params, query_shown=query,
                            claimed_value=claimed, computed_value=computed, tolerance=C.CLAIM_TOLERANCE, verdict=v,
                            reason=_reason(v, tool, claimed, computed, rel, params), evidence=ev,
                            confidence=_confidence(v, rel, n, C.CLAIM_TOLERANCE),
                            settle_with=None if v != "unprovable" else C.SETTLE_DEFAULT))
    return out


def overall_of(subs: list[SubClaim]) -> str:
    vs = {s.verdict for s in subs}
    return vs.pop() if len(vs) == 1 else ("unprovable" if not vs else "mixed")


def _overall_conf(subs: list[SubClaim]) -> float:
    if not subs:
        return 0.0
    checked = [s.confidence for s in subs if s.verdict != "unprovable"]
    base = sum(checked) / len(checked) if checked else 0.5
    return round(base * (0.85 + 0.15 * len(checked) / len(subs)), 3)


# ------------------------------------------------------------------ normalised restatement + mirror (templates)
def restate(s: SubClaim) -> str:
    b = s.params.get("booth_id", "?")
    cv = s.claimed_value
    if s.tool == "deletion_count":
        return (f"Booth {b} had more removals than expected" if s.params.get("mode") == "above_expected"
                else f"{cv:g} names were removed in Booth {b}" if cv is not None else f"Names were removed in Booth {b}")
    if s.tool == "addition_count":
        return (f"Booth {b} had more additions than expected" if s.params.get("mode") == "above_expected"
                else f"{cv:g} names were added in Booth {b}" if cv is not None else f"Names were added in Booth {b}")
    if s.tool == "compare_booths":
        what = "additions" if s.params.get("metric") == "added" else "removals"
        return f"Booth {b} had the most {what} of any booth"
    if s.tool == "deletion_rate":
        return f"{cv:g}% of names were removed in Booth {b}"
    if s.tool == "unanswerable":
        return "a part that cannot be measured from roll data"
    return f"{s.tool.replace('_', ' ')} in Booth {b}" + (f" is {cv:g}" if cv is not None else "")


FLIP = {"deletion_count": "addition_count", "addition_count": "deletion_count"}


def _pair_booth(direction_to: str, avoid: str | None) -> str:
    s = store()
    metric = "added" if direction_to == "add" else "deleted"
    order = sorted(s.agg, key=lambda x: -s.agg[x][metric])
    return next(b for b in order if b != avoid)


def mirror_of(subs_in: list[dict], subs_out: list[SubClaim], original: str) -> Mirror | None:
    tools = [s.tool for s in subs_out]
    if not any(t in FLIP or t == "compare_booths" for t in tools):
        return None
    direction_to = "add" if any(t == "deletion_count" or (t == "compare_booths" and s.params.get("metric") != "added")
                                for t, s in zip(tools, subs_out)) else "del"
    booths = [s.params.get("booth_id") for s in subs_out if s.params.get("booth_id")]
    pair = _pair_booth(direction_to, booths[0] if booths else None)
    flipped = []
    for si, so in zip(subs_in, subs_out):
        p = dict(so.params)
        if "booth_id" in p:
            p["booth_id"] = pair
        tool = so.tool
        if tool in FLIP:
            tool = FLIP[tool]
        if tool == "compare_booths":
            p["metric"] = "added" if p.get("metric", "deleted") == "deleted" else "deleted"
        flipped.append({"text": si["text"], "tool": tool, "params": p, "claimed_value": so.claimed_value,
                        "existence": si.get("existence"), "unknown": si.get("unknown")})
    m_out = execute(flipped, original, prefix="m")
    text = "; ".join(restate(s) for s in m_out)
    text, _ = guard(text[0].upper() + text[1:] if text else text, "claim", "en", template="Mirror claim (direction flipped).")
    identical = [s.tool == "unanswerable" for s in subs_out] == [s.tool == "unanswerable" for s in m_out] and \
        all(a.tolerance == b.tolerance for a, b in zip(subs_out, m_out))
    return Mirror(claim_text=text, sub_claim_verdicts=[s.verdict for s in m_out], identical_treatment=identical)


# ------------------------------------------------------------------ entry
def check(req: ClaimCheckRequest) -> ClaimVerdict:
    source, text = "text", (req.text or "").strip()
    if not text and req.image_b64:
        source = "image"
        got = llm.read_image(req.image_b64)
        text = (got or {}).get("text", "") if isinstance(got, dict) else ""
    lang = detect_lang(text) if text else "en"
    claim_id = hashlib.sha256(f"{source}|{text}|{req.mirror}".encode("utf-8")).hexdigest()[:12]
    if not text:
        msg = "Could not read a claim from this input (no vision model available offline). Please paste the text."
        return ClaimVerdict(claim_id=claim_id, input=ClaimInput(text="", source=source, lang="en"),
                            normalized_claim=msg, sub_claims=[], overall="unprovable", confidence=0.0,
                            guard=GuardResult(passed=True))
    safe = placeholders(text)
    subs_in, _how = split(safe)
    subs = execute(subs_in, safe)
    norm = "; ".join(restate(s) for s in subs if s.tool != "unanswerable")
    extra = sum(1 for s in subs if s.tool == "unanswerable")
    norm = (norm[0].upper() + norm[1:] if norm else "No measurable part") + (
        f" (+{extra} part{'s' if extra > 1 else ''} that cannot be measured from roll data)" if extra else "") + "."
    norm, g = guard(norm, "claim", "en", template="A claim about changes in the roll.")
    mirror = mirror_of(subs_in, subs, safe) if req.mirror else None
    return ClaimVerdict(claim_id=claim_id, input=ClaimInput(text=safe, source=source, lang=lang),
                        normalized_claim=norm, sub_claims=subs, overall=overall_of(subs),
                        confidence=_overall_conf(subs), mirror=mirror, guard=g)
