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
from bot import sarvam
from bot.texts import L, VERDICT, with_footer

ROOT = Path(__file__).resolve().parent.parent
API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.environ.get("BOT_API_TIMEOUT", "90"))


@dataclass
class Reply:
    kind: str  # "text" | "photo" | "voice"
    text: str = ""
    data: bytes = b""


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
    def __init__(self, base: str = API_BASE, client: httpx.AsyncClient | None = None):
        self.base = base
        self.client = client or httpx.AsyncClient(base_url=base, timeout=TIMEOUT)

    async def ask(self, text: str, lang: str | None = None) -> dict:
        r = await self.client.post("/citizen/ask", json={"text": text, "lang": lang, "channel": "telegram"})
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


def format_verdict(v: dict, lang: str) -> str:
    lines = [L["claim_head"][lang]]
    claim = (v.get("normalized_claim") or (v.get("input") or {}).get("text") or "").strip()
    if claim:
        lines.append(f"“{claim}”")
    lines.append("")
    for sc in v.get("sub_claims", []):
        label = VERDICT.get(sc.get("verdict"), {}).get(lang, sc.get("verdict", ""))
        lines.append(f"• {label}: {sc.get('text', '')}")
        if sc.get("reason"):
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


async def handle_text(api: Api, text: str) -> list[Reply]:
    text = (text or "").strip()
    if looks_like_claim(text):
        return await handle_claim(api, text=strip_claim_prefix(text) or text)
    lang = lang_of(text)
    try:
        a = await api.ask(text)
    except Exception:
        return [Reply("text", with_footer(L["api_down"][lang], lang))]
    return [Reply("text", with_footer(a.get("answer_text", ""), a.get("lang", lang)))]


async def handle_voice(api: Api, ogg: bytes) -> list[Reply]:
    """S3: OGG -> WAV 16k mono -> Sarvam STT (hi-IN) -> citizen flow -> Sarvam TTS voice note."""
    from api import constants as C
    if not sarvam.key():
        return [Reply("text", with_footer(C.VOICE_SOON["hi"], "hi"))]
    wav = sarvam.to_wav16k(ogg, ".ogg")
    transcript = sarvam.stt(wav, "hi") if wav else None
    if not transcript:
        return [Reply("text", with_footer(C.NO_QUERY["hi"], "hi"))]
    replies = await handle_text(api, transcript)
    if replies and replies[0].kind == "text":
        body = replies[0].text
        replies[0].text = f"« {transcript} »\n\n{body}"
        speak = body.split(C.PORTAL_LINE["hi"])[0].strip()
        voice = sarvam.tts_ogg(speak, lang_of(speak, "hi"))
        if voice:
            replies.append(Reply("voice", data=voice))
    return replies
