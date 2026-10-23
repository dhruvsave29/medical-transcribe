"""Contract + behaviour tests for POST /api/transcribe (Step 3)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conftest  # noqa: E402,F401

from app.main import app  # noqa: E402

from conftest import StubTranscriber, make_wav_pcm  # noqa: E402

client = TestClient(app)


@pytest.fixture()
def stub() -> StubTranscriber:
    stub = StubTranscriber()
    from app import asr_state

    original = asr_state.transcriber
    asr_state.transcriber = stub
    try:
        yield stub
    finally:
        asr_state.transcriber = original


def test_transcribe_contract(stub: StubTranscriber) -> None:
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", make_wav_pcm(1.5), "audio/wav")},
        data={"chunk_index": "3"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["chunk_index"] == 3
    assert body["text"] == "stub hello doctor"
    assert body["duration_ms"] == 1500


def test_transcribe_optional_language(stub: StubTranscriber) -> None:
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", make_wav_pcm(0.5), "audio/wav")},
        data={"chunk_index": "0", "language": "en"},
    )
    assert res.status_code == 200


def test_transcribe_empty_audio_is_400(stub: StubTranscriber) -> None:
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", b"", "audio/wav")},
        data={"chunk_index": "0"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "bad_request"


def test_transcribe_undecodable_audio_is_415(stub: StubTranscriber) -> None:
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", b"not a wav at all" * 100, "audio/wav")},
        data={"chunk_index": "0"},
    )
    assert res.status_code == 415
    body = res.json()
    assert body["error"]["code"] == "http_415"
    assert "message" in body["error"]


def test_transcribe_oversize_is_413(stub: StubTranscriber) -> None:
    big = b"\x00\x01" * (26 * 1024 * 1024 // 2)
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", big, "audio/wav")},
        data={"chunk_index": "0"},
    )
    assert res.status_code == 413


def test_transcribe_missing_chunk_index_is_422(stub: StubTranscriber) -> None:
    res = client.post(
        "/api/transcribe",
        files={"audio": ("chunk.wav", make_wav_pcm(0.3), "audio/wav")},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_transcribe_failure_is_503() -> None:
    class Broken(StubTranscriber):
        def transcribe(self, wav_bytes: bytes, language: str | None = None):
            raise RuntimeError("model exploded")

    broken = Broken()
    from app import asr_state

    original = asr_state.transcriber
    asr_state.transcriber = broken
    try:
        res = client.post(
            "/api/transcribe",
            files={"audio": ("chunk.wav", make_wav_pcm(0.3), "audio/wav")},
            data={"chunk_index": "0"},
        )
    finally:
        asr_state.transcriber = original
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "service_unavailable"

