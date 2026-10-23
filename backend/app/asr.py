"""Whisper ASR behind one Transcriber interface (PRD 3.1).

faster-whisper small.en runs locally on CPU (int8) — no API key, no cloud.
The model downloads on first backend start (auto-load thread) and inference
runs single-request-at-a-time so CTranslate2 stays happy. Transcript audio
is sensitive (PRD 3.4): nothing here logs transcript text, only sizes and
durations.
"""

from __future__ import annotations

import io
import logging
import os
import threading
import time

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

from .config import settings

logger = logging.getLogger("mediscript.asr")


class TranscriberError(Exception):
    """Raised when transcription cannot proceed (bad audio or model failure)."""


class Transcriber:
    """Interface for speech-to-text. Swap-friendly per PRD 3.1."""

    def transcribe(self, wav_bytes: bytes, language: str | None = None) -> tuple[str, float]:
        """Return (text, duration_seconds) for one speech segment."""
        raise NotImplementedError


_LOCK = threading.Lock()


class FasterWhisperTranscriber(Transcriber):
    """Local faster-whisper transcription with lazy singleton model."""

    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._started_at: float | None = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Download/init the model. Safe to call multiple times."""
        with _LOCK:
            if self._model is not None:
                return
            started = time.monotonic()
            logger.info(
                "loading ASR model=%s device=%s compute=%s cpu_threads=%s",
                settings.whisper_model,
                settings.whisper_device,
                settings.whisper_compute_type,
                settings.whisper_cpu_threads,
            )
            self._model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                cpu_threads=settings.whisper_cpu_threads,
                download_root=None,
            )
            self._started_at = time.monotonic()
            logger.info("ASR model ready in %.1fs", self._started_at - started)

    def _model_or_fail(self) -> WhisperModel:
        if self._model is None:
            # First use may arrive before the preload thread finishes;
            # load inline so the request still succeeds.
            self.load()
        assert self._model is not None
        return self._model

    def transcribe(self, wav_bytes: bytes, language: str | None = None) -> tuple[str, float]:
        model = self._model_or_fail()
        try:
            audio = decode_audio(io.BytesIO(wav_bytes), sampling_rate=16000)
        except Exception as exc:  # invalid container / truncated file
            raise TranscriberError(f"audio decode failed: {type(exc).__name__}") from exc
        duration = float(audio.shape[0] / 16000)
        if duration < 0.05:
            raise TranscriberError("audio too short")

        forced = None
        if settings.whisper_model.endswith(".en"):
            forced = "en"
        elif language:
            forced = language

        started = time.monotonic()
        segments, info = model.transcribe(
            audio,
            language=forced,
            beam_size=settings.whisper_beam_size,
            vad_filter=False,  # browser VAD already removed silence
        )
        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
        elapsed = time.monotonic() - started
        logger.info(
            "transcribed duration=%.2fs took=%.2fs chars=%d lang=%s",
            duration,
            elapsed,
            len(text),
            info.language,
        )
        return text.strip(), duration


def get_transcriber() -> Transcriber:
    from .asr_state import transcriber

    return transcriber


def maybe_autoload() -> None:
    """Start the download/load in the background on first backend start."""
    if not _autoload_enabled():
        logger.info("ASR auto-load disabled; model loads on first /api/transcribe")
        return
    thread = threading.Thread(target=_autoload_worker, name="asr-autoload", daemon=True)
    thread.start()


def _autoload_enabled() -> bool:
    return os.environ.get("MEDISCRIPT_ASR_AUTOLOAD", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _autoload_worker() -> None:
    from .asr_state import transcriber

    try:
        transcriber.load()
    except Exception:
        logger.exception("ASR model preload failed — it will retry on first request")
