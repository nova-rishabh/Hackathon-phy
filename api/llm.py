"""One LLM client: Claude (tool use, temperature 0) -> Gemini -> None (caller uses its template).

Every call is cached on disk in cache/llm/<sha256(model+prompt+input)>.json. Under DEMO_MODE=1 only
the cache is read; a miss returns None so the caller falls back to its template. Without API keys the
client never touches the network. The LLM never produces numbers that are shown: callers only use it
to split claims, read images and phrase text.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from api import constants as C
from api.ops import record_llm

ROOT = Path(__file__).resolve().parent.parent


def demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "0") == "1"


def cache_dir() -> Path:
    return Path(os.environ.get("ROLLWATCH_CACHE", ROOT / "cache" / "llm"))


def cache_count() -> int:
    d = cache_dir()
    return len(list(d.glob("*.json"))) if d.exists() else 0


def _key(model: str, prompt: str, payload) -> str:
    raw = model + "\n" + prompt + "\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(k: str):
    p = cache_dir() / f"{k}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _cache_put(k: str, value: dict):
    try:
        d = cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{k}.json").write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def _claude(model, system, user, tool, image_b64):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=20.0)
    content = []
    if image_b64:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}})
    content.append({"type": "text", "text": user})
    msg = client.messages.create(model=model, max_tokens=1024, temperature=0, system=system,
                                 messages=[{"role": "user", "content": content}],
                                 tools=[tool], tool_choice={"type": "tool", "name": tool["name"]})
    out = next((b.input for b in msg.content if getattr(b, "type", "") == "tool_use"), None)
    return out, msg.usage.input_tokens, msg.usage.output_tokens


def _gemini(system, user, tool, image_b64):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    parts = [types.Part.from_text(text=user + "\nReturn JSON matching this schema: "
                                  + json.dumps(tool["input_schema"], ensure_ascii=False))]
    if image_b64:
        parts.append(types.Part.from_bytes(data=base64.b64decode(image_b64), mime_type="image/png"))
    resp = client.models.generate_content(
        model=C.MODEL_GEMINI, contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(system_instruction=system, temperature=0,
                                           response_mime_type="application/json"))
    um = resp.usage_metadata
    return json.loads(resp.text), getattr(um, "prompt_token_count", 0) or 0, getattr(um, "candidates_token_count", 0) or 0


def call(model: str, system: str, user: str, tool: dict, image_b64: str | None = None) -> dict | None:
    """Return the tool input dict, or None (caller falls back to its template/rule path)."""
    payload = {"user": user, "tool": tool, "img": hashlib.sha256((image_b64 or "").encode()).hexdigest()}
    k = _key(model, system, payload)
    hit = _cache_get(k)
    if hit is not None:
        record_llm(hit.get("model", model), hit.get("tokens_in", 0), hit.get("tokens_out", 0), True)
        return hit.get("output")
    if demo_mode() or not available():
        return None
    out, tin, tout, used = None, 0, 0, model
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            out, tin, tout = _claude(model, system, user, tool, image_b64)
        except Exception:  # network, quota, bad key: fall through
            out = None
    if out is None and os.environ.get("GEMINI_API_KEY"):
        try:
            out, tin, tout = _gemini(system, user, tool, image_b64)
            used = C.MODEL_GEMINI
        except Exception:
            out = None
    if out is None:
        return None
    record_llm(used, tin, tout, False)
    _cache_put(k, {"model": used, "tokens_in": tin, "tokens_out": tout, "output": out})
    return out


# ------------------------------------------------------------------ task helpers
PHRASE_TOOL = {
    "name": "phrase", "description": "Return the rewritten text.",
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
}


def phrase(text: str, lang: str, instruction: str = "Rewrite this in plain, calm language.") -> str | None:
    sys_p = (f"{instruction} Language: {lang}. Keep every number exactly. Never name parties, people, "
             "institutions, religions, castes or communities. Never use words implying fraud or intent.")
    out = call(C.MODEL_PHRASE, sys_p, text, PHRASE_TOOL)
    return out.get("text") if isinstance(out, dict) and isinstance(out.get("text"), str) else None


def rewrite_neutral(text: str, lang: str) -> str | None:
    return phrase(text, lang, "Rewrite neutrally, with no actors and no blame, keeping the numbers.")


READ_TOOL = {
    "name": "read_image", "description": "Transcribe the claim text in the image.",
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"},
                                                       "lang": {"type": "string", "enum": ["hi", "en", "pa"]}},
                     "required": ["text", "lang"]},
}


def read_image(image_b64: str) -> dict | None:
    return call(C.MODEL_SPLIT, "Transcribe the forwarded message in this screenshot exactly.", "image", READ_TOOL, image_b64)
