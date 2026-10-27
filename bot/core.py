"""Transport-agnostic bot logic: a thin HTTP client over the RollWatch API.

Handlers return a list of Reply objects; bot/app.py turns them into Telegram messages. This keeps the
logic testable offline (bot/smoke_checks.py drives it against the in-process FastAPI app).
"""
import base64
import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

from api.normalize import has_devanagari, has_gurmukhi
from bot import audio
from bot.texts import L, VERDICT, with_footer

ROOT = Path(__file__).resolve().parent.parent
API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.environ.get("BOT_API_TIMEOUT", "90"))


@dataclass
class Reply:
    kind: str  # "text" | "photo" | "voice" | "audio"
    text: str = ""
    data: bytes = b""
    answer: dict | None = None  # the citizen answer behind a text reply (for the spoken version)


def lang_of(text: str | None, default: str = "en") -> str:
    """Language follows the user's script."""
    if has_devanagari(text or ""):
        return "hi"
    if has_gurmukhi(text or ""):
        return "pa"
    return default


# a message "starts with a claim": explicit prefix, or count/change words typical of a forward
_CLAIM_PREFIX = re.compile(r"^\s*(?:claim|check|fact\s*check|दावा|जाँच|जांच|ਦਾਅਵਾ)\s*[:\-]", re.I)
_CLAIM_WORDS = re.compile(
    r"\b(?:deleted|removed|cut|kaat|kaate|kat|hata|hataye|added|ghost|fake|bogus|names?\s+(?:cut|removed|deleted)"
    r"|most|sabse|zyada|lakh|thousand|percent|%)\b|काट|हटा|जोड़|फर्जी|फ़र्ज़ी|सबसे|ਕੱਟ|ਹਟਾ|ਜੋੜ",
    re.I)


def looks_like_claim(text: str) -> bool:
    t = text or ""
    if _CLAIM_PREFIX.match(t):
        return True
    return bool(re.search(r"\d", t)) and len(_CLAIM_WORDS.findall(t)) >= 1 and len(t.split()) >= 5


def strip_claim_prefix(text: str) -> str:
    return _CLAIM_PREFIX.sub("", text or "", count=1).strip()


class Api:
    def __init__(self, base: str = API_BASE, client: httpx.AsyncClient | None = None, channel: str = "telegram"):
        self.base, self.channel = base, channel
        self.client = client or httpx.AsyncClient(base_url=base, timeout=TIMEOUT)

    async def ask(self, text: str, lang: str | None = None) -> dict:
        r = await self.client.post("/citizen/ask", json={"text": text, "lang": lang, "channel": self.channel})
        r.raise_for_status()
        return r.json()

    async def documents(self, dob: str | None, lang: str) -> dict:
        r = await self.client.get("/documents", params={"lang": lang, **({"dob": dob} if dob else {})})
        r.raise_for_status()
        return r.json()

    async def claim(self, text: str | None = None, image: bytes | None = None) -> dict:
        body = {"mirror": True}
        if text:
            body["text"] = text
        if image:
            body["image_b64"] = base64.b64encode(image).decode("ascii")
        r = await self.client.post("/claims/check", json=body)
        r.raise_for_status()
        return r.json()

    async def card(self, v: dict) -> bytes | None:
        """card_png may be an absolute URL, an API path (/cards/x.png) or a repo-relative path."""
        ref = v.get("card_png")
        if not ref:
            return None
        cands = []
        if ref.startswith("http"):
            cands.append(ref)
        else:
            for p in (ROOT / ref.lstrip("/"), ROOT / "cards" / Path(ref).name):
                if p.is_file():
                    return p.read_bytes()
            cands.append(ref if ref.startswith("/") else "/" + ref)
        cands.append(f"/cards/{v.get('claim_id')}.png")
        for u in cands:
            try:
                r = await self.client.get(u)
                if r.status_code == 200 and r.content[:4] == b"\x89PNG":
                    return r.content
            except httpx.HTTPError:
                continue
        return None


def guard_ok(text: str, strict: bool = False) -> bool:
    """Outbound check through api/guard.py (in-process). Without the guard module, non-strict text
    (already guarded by the API) passes and strict text (raw user input echoed back) is dropped."""
    try:
        from api import guard
    except Exception:
        return not strict
    try:
        g = guard.check(text, surface="bot")
        return bool(g.passed if hasattr(g, "passed") else dict(g).get("passed"))
    except Exception:
        return False


def format_verdict(v: dict, lang: str) -> str:
    lines = [L["claim_head"][lang]]
    claim = (v.get("normalized_claim") or (v.get("input") or {}).get("text") or "").strip()
    if claim and guard_ok(claim, strict=True):
        lines.append(f"“{claim}”")
    lines.append("")
    for sc in v.get("sub_claims", []):
        label = VERDICT.get(sc.get("verdict"), {}).get(lang, sc.get("verdict", ""))
        txt = sc.get("text", "")
        lines.append(f"• {label}: {txt}" if txt and guard_ok(txt) else f"• {label}")
        if sc.get("reason") and guard_ok(sc["reason"]):
            lines.append(f"  {sc['reason']}")
    overall = VERDICT.get(v.get("overall"), {}).get(lang, v.get("overall", ""))
    lines += ["", L["overall"][lang].format(v=overall, pct=round(100 * float(v.get("confidence", 0))))]
    m = v.get("mirror")
    if m and m.get("identical_treatment"):
        lines.append(L["mirror"][lang])
    lines.append(L["review"][lang])
    return with_footer("\n".join(lines), lang)


async def handle_claim(api: Api, text: str | None = None, image: bytes | None = None,
                       lang: str | None = None) -> list[Reply]:
    lang = lang or lang_of(text)
    try:
        v = await api.claim(text=text, image=image)
    except Exception:
        return [Reply("text", with_footer(L["api_down"][lang], lang))]
    if image and not text:  # language of the screenshot's text, as read by the API
        lang = (v.get("input") or {}).get("lang") or lang_of(v.get("normalized_claim"), lang)
        if lang not in ("hi", "en", "pa"):
            lang = "hi"
    out = [Reply("text", format_verdict(v, lang))]
    png = await api.card(v)
    if png:
        out.append(Reply("photo", data=png))
    return out


# A greeting or a "what is this" gets the welcome, not a name search.
_GREETING = re.compile(r"^\W*(hi+|hello|hey|hii+|namaste|namaskar|helo|start|help|menu|sat\s*sri\s*akal|"
                       r"नमस्ते|नमस्कार|हाय|हेलो|ਸਤ ਸ੍ਰੀ ਅਕਾਲ|ਹੈਲੋ|/start|/help)\W*$", re.I)


# "documents" / "दस्तावेज़" (optionally with a date of birth): which documents a notice would ask for.
_DOCS = re.compile(r"(documents?|docs|kagaz|kaagaz|dastavez|दस्तावेज़?|दस्तावेज|कागज़?|कागज|ਦਸਤਾਵੇਜ਼|ਦਸਤਾਵੇਜ|ਕਾਗਜ਼)", re.I)
_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b|\b(\d{4})-(\d{2})-(\d{2})\b")


def _dob(text: str) -> str | None:
    m = _DATE.search(text or "")
    if not m:
        return None
    d, mo, y = (m.group(1), m.group(2), m.group(3)) if m.group(3) else (m.group(6), m.group(5), m.group(4))
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


async def handle_documents(api: Api, text: str) -> list[Reply]:
    lang = lang_of(text)
    try:
        d = await api.documents(_dob(text), lang)
    except Exception:
        return [Reply("text", with_footer(L["api_down"][lang], lang))]
    body = "\n".join(d["lines"]) + "\n\n" + d["list"] + "\n" + "\n".join(d["other"])
    return [Reply("text", with_footer(body, lang))]


async def handle_text(api: Api, text: str) -> list[Reply]:
    text = (text or "").strip()
    if not text or _GREETING.match(text):
        lang = lang_of(text) if text else "en"
        return [Reply("text", with_footer(L["start"][lang], lang))]
    if _DOCS.search(text) and len(text) < 60:
        return await handle_documents(api, text)
    if looks_like_claim(text):
        return await handle_claim(api, text=strip_claim_prefix(text) or text)
    lang = lang_of(text)
    try:
        a = await api.ask(text)
    except Exception:
        return [Reply("text", with_footer(L["api_down"][lang], lang))]
    body = a.get("answer_text", "")
    if not (a.get("guard") or {}).get("passed", True):  # templated text is guard-exempt (TRD 6)
        body = L["api_down"][a.get("lang", lang)]
    return [Reply("text", with_footer(body, a.get("lang", lang)), answer=a)]


def spoken_reply(a: dict, lang: str) -> str:
    """What a helpful person would say: status, reason, the one thing to do, helpline, scam line.
    Built only from fixed templates (api/constants.SPOKEN) plus the citizen's own name and booth."""
    from api import constants as C
    S = C.SPOKEN
    lang = "en" if lang == "en" else "hi"  # Punjabi is spoken in Hindi: the voice model has no Punjabi
    status, reason, m = a.get("status"), a.get("reason_category"), a.get("match") or {}
    if status == "not_found" or not m:
        return " ".join([S["hello"][lang], S["not_found"][lang]])
    name = (m.get("name_dev") if lang == "hi" else m.get("name_lat")) or m.get("name_lat") or ""
    booth = int(str(m.get("booth_id", "B0"))[1:] or 0)
    parts = [S["hello"][lang], S[status][lang].format(name=name, booth=booth)]
    if status != "present" and reason in S["reason"]:
        parts.append(S["reason"][reason][lang].format(booth=booth))
    if status == "not_in_new_list":
        parts.append(S["do_not_in_list"][lang])
    elif status == "modified":
        parts.append(S["do_modified"][lang])
    if status != "present":
        parts.append(S["helpline"][lang])
    parts.append(S["scam"][lang])
    return " ".join(parts)


async def handle_voice(api: Api, ogg: bytes) -> list[Reply]:
    """S3: Telegram OGG -> ElevenLabs STT (scribe_v1) -> citizen flow -> ElevenLabs TTS voice note.
    Without ELEVENLABS_API_KEY: a text reply."""
    from api import constants as C
    from api import voice
    if not voice.available():
        return [Reply("text", with_footer(C.VOICE_SOON["hi"], "hi"))]
    heard = voice.stt(ogg, "audio/ogg")
    transcript = (heard or {}).get("text")
    if not transcript:
        return [Reply("text", with_footer(C.NO_QUERY["hi"], "hi"))]
    replies = await handle_text(api, transcript)
    if replies and replies[0].kind == "text":
        body = replies[0].text
        replies[0].text = f"« {transcript} »\n\n{body}"
        a = replies[0].answer
        if a:  # a name lookup: speak it like a person, from fixed templates (guard-exempt, TRD 6)
            lang = "en" if a.get("lang") == "en" else "hi"
            mp3 = voice.tts_mp3(spoken_reply(a, lang), lang, guarded=True)
        else:  # a claim or a fallback: read the (guarded) written text
            speak = body.split(C.PORTAL_LINE["hi"])[0].strip()
            mp3 = voice.tts_mp3(speak, lang_of(speak, (heard or {}).get("lang", "hi")))
        if mp3:
            ogg_out = audio.to_ogg_opus(mp3)
            replies.append(Reply("voice", data=ogg_out) if ogg_out else Reply("audio", data=mp3))
    return replies
