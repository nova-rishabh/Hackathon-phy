"""ffmpeg helper for Telegram voice notes (OGG/Opus). Speech itself is ElevenLabs, via api/voice.py."""
import subprocess
import tempfile
from pathlib import Path


def to_ogg_opus(audio: bytes, in_suffix: str = ".mp3") -> bytes | None:
    """MP3 (or any ffmpeg input) -> OGG/Opus, the format Telegram needs for a voice note. None if no ffmpeg."""
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / ("in" + in_suffix), Path(d) / "out.ogg"
        src.write_bytes(audio)
        try:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-c:a", "libopus",
                            "-b:a", "32k", str(dst)], check=True, timeout=60, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            return None
        return dst.read_bytes() if dst.exists() else None
