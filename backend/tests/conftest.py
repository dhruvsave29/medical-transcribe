"""Shared test fixtures: stub the ASR model so tests never touch the network.

MEDISCRIPT_ASR_AUTOLOAD=0 is set before importing the app so the background
preload never starts in tests.
"""

import io
import os
import sys
import wave
from pathlib import Path

os.environ["MEDISCRIPT_ASR_AUTOLOAD"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.asr import Transcriber  # noqa: E402


class StubTranscriber(Transcriber):
    """Deterministic in-memory transcriber for contract tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, float]] = []
        self.ready = True

    @property
    def is_ready(self) -> bool:  # type: ignore[override]
        return self.ready

    def transcribe(self, wav_bytes: bytes, language: str | None = None) -> tuple[str, float]:
        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as w:
                duration = w.getnframes() / w.getframerate()
        except Exception as exc:
            from app.asr import TranscriberError

            raise TranscriberError(f"audio decode failed: {type(exc).__name__}") from exc
        self.calls.append((duration, float(len(wav_bytes))))
        return "stub hello doctor", duration


def make_wav_pcm(seconds: float = 1.0, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x01" * int(seconds * rate))
    return buf.getvalue()
