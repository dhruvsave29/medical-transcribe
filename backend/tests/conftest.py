"""Shared test fixtures: stub ASR + analyzer so tests never touch the network.

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

from app.analyzer import AnalyzerError, Analyzer  # noqa: E402
from app.asr import Transcriber  # noqa: E402
from app.summary import ClinicalSummary  # noqa: E402


class StubTranscriber(Transcriber):
    """Deterministic in-memory transcriber for contract tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []
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


class StubAnalyzer(Analyzer):
    """Deterministic analyzer for contract tests."""

    def __init__(self) -> None:
        self.fail = False
        self.chat_fail = False
        self.chat_calls: list[tuple[str, str, str]] = []

    def analyze(self, transcript: str) -> ClinicalSummary:
        if self.fail:
            raise AnalyzerError("LLM output did not match the clinical summary schema")
        return sample_summary()

    def chat(self, transcript: str, summary_json: str, message: str) -> str:
        if self.chat_fail:
            raise AnalyzerError("local LLM chat request failed")
        self.chat_calls.append((transcript, summary_json, message))
        return "The transcript reports chest heaviness for three months."


def sample_summary() -> ClinicalSummary:
    return ClinicalSummary.model_validate(
        {
            "patient": {"name": None, "age": None, "sex": None, "identifiers": []},
            "chief_complaints": [],
            "symptoms": {"positive": [], "negative": []},
            "clinical_summary": "stub summary paragraph",
        }
    )


def make_wav_pcm(seconds: float = 1.0, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x01" * int(seconds * rate))
    return buf.getvalue()
