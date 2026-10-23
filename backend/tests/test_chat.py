"""Contract + behaviour tests for POST /api/chat (Step 5)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conftest  # noqa: E402,F401

from app.main import app  # noqa: E402

from conftest import StubAnalyzer, sample_summary  # noqa: E402

client = TestClient(app)

TRANSCRIPT = "The patient reports chest heaviness for three months."


@pytest.fixture()
def stub() -> StubAnalyzer:
    stub = StubAnalyzer()
    from app import analyzer_state

    original = analyzer_state.analyzer
    analyzer_state.analyzer = stub
    try:
        yield stub
    finally:
        analyzer_state.analyzer = original


def test_chat_contract_with_summary(stub: StubAnalyzer) -> None:
    summary = sample_summary().model_dump(mode="json")
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "summary": summary, "message": "What is the complaint?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {"reply"}
    assert "chest heaviness" in body["reply"]
    # summary reached the analyzer as JSON string
    t, s, m = stub.chat_calls[0]
    assert "chest heaviness" in t and "clinical_summary" in s and "complaint" in m


def test_chat_contract_without_summary(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "summary": None, "message": "Age?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["reply"]
    _, s, _ = stub.chat_calls[0]
    assert s == ""  # no summary → empty context section


def test_chat_whitespace_message_422(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "message": "   "},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_chat_empty_transcript_400(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/chat",
        json={"transcript": "", "message": "What?"},
    )
    assert res.status_code == 400


def test_chat_bad_summary_422(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "summary": {"patient": "nope"}, "message": "Age?"},
    )
    assert res.status_code == 422
    assert "summary" in res.json()["error"]["message"]


def test_chat_llm_failure_503(stub: StubAnalyzer) -> None:
    stub.chat_fail = True
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "message": "Age?"},
    )
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "service_unavailable"


def test_chat_not_a_summary_string_ignored(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/chat",
        json={"transcript": TRANSCRIPT, "summary": "plain string", "message": "Age?"},
    )
    # plain string is neither null nor a valid object — must be rejected
    assert res.status_code == 422
