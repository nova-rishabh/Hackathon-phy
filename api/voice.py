"""Voice via ElevenLabs (plain HTTP): TTS eleven_multilingual_v2, STT scribe_v1.

Key: X-ElevenLabs-Key (BYOK, per request) or ELEVENLABS_API_KEY. Without one, the endpoints return 503
and the helpers return None, so callers fall back to text. TTS text passes api/guard.py first and the
audio is cached by sha256 under cache/tts/, so a replayed answer costs nothing.
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from api import constants as C
from api import guard, keys

ROOT = Path(__file__).resolve().parent.parent
TTS_CACHE = ROOT / "cache" / "tts"
BASE = "https://api.elevenlabs.io/v1"
TIMEOUT = float(os.environ.get("ELEVENLABS_TIMEOUT_S", "30"))
_LANG_BACK = {v: k for k, v in C.ELEVEN_LANG.items()} | {"hi": "hi", "en": "en", "pa": "pa"}
NO_KEY = {"error": "voice_unavailable",
          "message": "No ElevenLabs key. Send X-ElevenLabs-Key or set ELEVENLABS_API_KEY on the server."}

router = APIRouter()


def available() -> bool:
    return bool(keys.get("elevenlabs"))


def _cache_path(text: str, lang: str) -> Path:
    h = hashlib.sha256(f"{C.ELEVEN_TTS_MODEL}|{C.ELEVEN_VOICE_ID}|{lang}|{text}".encode("utf-8")).hexdigest()
    return TTS_CACHE / f"{h}.mp3"


def safe_text(text: str, lang: str) -> str:
    t, _ = guard.guard((text or "").strip(), surface="citizen", lang=lang)
    return t[:C.TTS_MAX_CHARS]


def tts_mp3(text: str, lang: str = "hi", guarded: bool = False) -> bytes | None:
    """Guarded text -> MP3 bytes. Cache first, then ElevenLabs (needs key). None on no key / error."""
    text = text if guarded else safe_text(text, lang)
    if not text:
        return None
    p = _cache_path(text, lang)
    if p.exists():
        return p.read_bytes()
    k = keys.get("elevenlabs")
    if not k:
        return None
    try:
        r = httpx.post(f"{BASE}/text-to-speech/{C.ELEVEN_VOICE_ID}",
                       params={"output_format": "mp3_44100_128"},
                       headers={"xi-api-key": k, "accept": "audio/mpeg"},
                       json={"text": text, "model_id": C.ELEVEN_TTS_MODEL}, timeout=TIMEOUT)
        r.raise_for_status()
        audio = r.content
    except Exception:
        return None
    if audio:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(audio)
        except OSError:
            pass
    return audio or None


def stt(audio: bytes, mime: str = "audio/ogg", lang: str | None = None) -> dict | None:
    """Any audio (webm/ogg/mp3/wav) -> {"text", "lang"}. None on no key / error / empty transcript."""
    k = keys.get("elevenlabs")
    if not k or not audio:
        return None
    data = {"model_id": C.ELEVEN_STT_MODEL}
    if lang in C.ELEVEN_LANG:
        data["language_code"] = C.ELEVEN_LANG[lang]
    ext = (mime or "audio/ogg").split("/")[-1].split(";")[0] or "ogg"
    try:
        r = httpx.post(f"{BASE}/speech-to-text", headers={"xi-api-key": k}, data=data,
                       files={"file": (f"voice.{ext}", audio, mime or "application/octet-stream")}, timeout=TIMEOUT)
        r.raise_for_status()
        j = r.json()
    except Exception:
        return None
    text = (j.get("text") or "").strip()
    if not text:
        return None
    code = (j.get("language_code") or "").lower()
    return {"text": text, "lang": _LANG_BACK.get(code, lang or "hi")}


# ------------------------------------------------------------------ endpoints
class TTSRequest(BaseModel):
    text: str
    lang: str = "hi"


class STTRequest(BaseModel):
    audio_b64: str
    mime: str = "audio/webm"
    lang: str | None = None  # optional hint ("hi" | "en" | "pa"); auto-detect when absent


@router.post("/voice/tts")
def voice_tts(req: TTSRequest):
    lang = req.lang if req.lang in ("hi", "en", "pa") else "hi"
    if not req.text.strip():
        raise HTTPException(422, "text is empty")
    text = safe_text(req.text, lang)
    if not _cache_path(text, lang).exists() and not available():
        return JSONResponse(NO_KEY, status_code=503)
    audio = tts_mp3(text, lang, guarded=True)
    if not audio:
        return JSONResponse({"error": "voice_failed", "message": "Text-to-speech failed; show the text reply."},
                            status_code=503)
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/voice/stt")
def voice_stt(req: STTRequest):
    if not available():
        return JSONResponse(NO_KEY, status_code=503)
    try:
        raw = base64.b64decode(req.audio_b64.split(",")[-1])  # accepts a data: URL too
    except Exception:
        raise HTTPException(422, "audio_b64 is not valid base64")
    out = stt(raw, req.mime, req.lang)
    if out is None:
        return JSONResponse({"error": "voice_failed", "message": "Speech-to-text failed; please type instead."},
                            status_code=503)
    return out
