"""Smoke tests for /api/health and the global error contract (Step 1/3)."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conftest  # noqa: E402,F401  (sets MEDISCRIPT_ASR_AUTOLOAD=0)

from app.main import app  # noqa: E402

import conftest  # noqa: E402,F401

client = TestClient(app)


def test_health_contract() -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["asr"].startswith("faster-whisper/")
    assert body["llm"].startswith("ollama/")
    assert isinstance(body["model_ready"], bool)


def test_health_model_ready_after_load() -> None:
    from app.asr_state import transcriber

    transcriber._model = object()  # type: ignore[assignment]  # force-ready
    try:
        body = client.get("/api/health").json()
        assert body["model_ready"] is True
    finally:
        transcriber._model = None


def test_unknown_route_uses_error_contract() -> None:
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "not_found"
    assert "message" in body["error"]

