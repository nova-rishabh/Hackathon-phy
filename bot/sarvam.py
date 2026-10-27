"""S3 voice: ffmpeg + Sarvam STT/TTS. Everything needs SARVAM_API_KEY; without it every call returns None.

Pre-generated TTS for scripted replies: cache/tts/<sha1(text)[:16]>.ogg (OGG/Opus) is used first, so the
demo needs no key for those. `python -m bot.sarvam --pregen "text" ...` fills it when a key is set.
"""
import base64
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
TTS_CACHE = ROOT / "cache" / "tts"
STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
STT_MODEL = os.environ.get("SARVAM_STT_MODEL", "saarika:v2.5")
TTS_MODEL = os.environ.get("SARVAM_TTS_MODEL", "bulbul:v2")
TTS_SPEAKER = os.environ.get("SARVAM_TTS_SPEAKER", "anushka")
LANG_CODE = {"hi": "hi-IN", "en": "en-IN", "pa": "pa-IN"}
TTS_MAX_CHARS = 1400


def key() -> str | None:
    return os.environ.get("SARVAM_API_KEY") or None


def _ffmpeg(args: list[str], data: bytes, in_suffix: str, out_suffix: str) -> bytes | None:
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / ("in" + in_suffix), Path(d) / ("out" + out_suffix)
        src.write_bytes(data)
        try:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), *args, str(dst)],
                           check=True, timeout=60, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            return None
        return dst.read_bytes() if dst.exists() else None


def to_wav16k(audio: bytes, suffix: str = ".ogg") -> bytes | None:
    """Telegram OGG/Opus (or any ffmpeg input) -> WAV 16 kHz mono PCM."""
    return _ffmpeg(["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le"], audio, suffix, ".wav")


def to_ogg_opus(wav: bytes) -> bytes | None:
    """WAV -> OGG/Opus, the format Telegram needs for a voice note."""
    return _ffmpeg(["-ac", "1", "-c:a", "libopus", "-b:a", "32k"], wav, ".wav", ".ogg")


def stt(wav16k: bytes, lang: str = "hi") -> str | None:
    k = key()
    if not k or not wav16k:
        return None
    try:
        r = httpx.post(STT_URL, headers={"api-subscription-key": k},
                       files={"file": ("voice.wav", wav16k, "audio/wav")},
                       data={"model": STT_MODEL, "language_code": LANG_CODE.get(lang, "hi-IN")},
                       timeout=60)
        r.raise_for_status()
        return (r.json().get("transcript") or "").strip() or None
    except Exception:
        return None


def stt_any(audio: bytes, lang: str = "hi") -> str | None:
    """Any audio container (web upload / Telegram OGG) -> transcript."""
    if not key():
        return None
    wav = to_wav16k(audio, ".bin")
    return stt(wav, lang) if wav else None


def _cache_path(text: str, lang: str) -> Path:
    h = hashlib.sha1(f"{lang}|{text}".encode("utf-8")).hexdigest()[:16]
    return TTS_CACHE / f"{h}.ogg"


def tts_ogg(text: str, lang: str = "hi") -> bytes | None:
    """Text -> OGG/Opus voice note. Cache first, then Sarvam (needs key)."""
    text = (text or "").strip()[:TTS_MAX_CHARS]
    if not text:
        return None
    p = _cache_path(text, lang)
    if p.exists():
        return p.read_bytes()
    k = key()
    if not k:
        return None
    try:
        r = httpx.post(TTS_URL, headers={"api-subscription-key": k},
                       json={"text": text, "target_language_code": LANG_CODE.get(lang, "hi-IN"),
                             "speaker": TTS_SPEAKER, "model": TTS_MODEL},
                       timeout=60)
        r.raise_for_status()
        audios = r.json().get("audios") or []
        if not audios:
            return None
        ogg = to_ogg_opus(base64.b64decode(audios[0]))
    except Exception:
        return None
    if ogg:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(ogg)
        except OSError:
            pass
    return ogg


if __name__ == "__main__":  # python -m bot.sarvam --pregen "text 1" "text 2"
    if len(sys.argv) > 2 and sys.argv[1] == "--pregen":
        if not key():
            sys.exit("SARVAM_API_KEY is not set; cannot pre-generate TTS.")
        for t in sys.argv[2:]:
            print(_cache_path(t[:TTS_MAX_CHARS], "hi"), "ok" if tts_ogg(t, "hi") else "failed")
