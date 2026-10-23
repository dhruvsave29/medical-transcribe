"""Process-wide ASR singleton (kept out of asr.py so tests can substitute)."""

from .asr import FasterWhisperTranscriber

transcriber = FasterWhisperTranscriber()
