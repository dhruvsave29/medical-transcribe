"""Smoke tests for the health endpoint (Step 1)."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_contract() -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["asr"].startswith("faster-whisper/")
    assert body["llm"].startswith("ollama/")
    assert body["model_ready"] is False


def test_unknown_route_uses_error_contract() -> None:
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "not_found"
    assert "message" in body["error"]
