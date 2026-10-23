"""Contract + behaviour tests for POST /api/analyze (Step 4)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conftest  # noqa: E402,F401

from app.main import app  # noqa: E402

from conftest import StubAnalyzer, sample_summary  # noqa: E402

client = TestClient(app)


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


def test_analyze_contract(stub: StubAnalyzer) -> None:
    res = client.post("/api/analyze", json={"transcript": "Consultation text."})
    assert res.status_code == 200
    body = res.json()
    assert body["patient"]["name"] is None
    assert body["clinical_summary"] == "stub summary paragraph"
    assert body["symptoms"] == {"positive": [], "negative": []}


def test_analyze_empty_transcript_400(stub: StubAnalyzer) -> None:
    res = client.post("/api/analyze", json={"transcript": "   "})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "bad_request"


def test_analyze_missing_field_422(stub: StubAnalyzer) -> None:
    res = client.post("/api/analyze", json={"text": "wrong key"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_analyze_bad_json_400(stub: StubAnalyzer) -> None:
    res = client.post(
        "/api/analyze", content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400


def test_analyze_llm_failure_is_503() -> None:
    fail_stub = StubAnalyzer()
    fail_stub.fail = True
    from app import analyzer_state

    original = analyzer_state.analyzer
    analyzer_state.analyzer = fail_stub
    try:
        res = client.post("/api/analyze", json={"transcript": "Consultation text."})
    finally:
        analyzer_state.analyzer = original
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "service_unavailable"


def test_analyze_unreachable_llm_is_503() -> None:
    """Real OllamaAnalyzer against a dead endpoint → 503 error contract."""
    from app import analyzer_state, config

    real = analyzer_state.analyzer
    saved = config.settings.llm_base_url
    config.settings.llm_base_url = "http://127.0.0.1:9/v1"  # closed port
    try:
        analyzer_state.analyzer._client = None  # rebuild client against dead port
        res = client.post("/api/analyze", json={"transcript": "Consultation text."})
        assert res.status_code == 503
        assert res.json()["error"]["code"] == "service_unavailable"
    finally:
        config.settings.llm_base_url = saved
        analyzer_state.analyzer._client = None
        analyzer_state.analyzer = real


def test_analyze_never_invents_fields(stub: StubAnalyzer) -> None:
    """Summary only contains PRD keys."""
    res = client.post("/api/analyze", json={"transcript": "Consultation text."})
    body = res.json()
    expected = {
        "patient",
        "chief_complaints",
        "history_of_present_illness",
        "symptoms",
        "past_medical_history",
        "medications",
        "allergies",
        "clinical_observations",
        "assessment",
        "plan",
        "clinical_summary",
    }
    assert set(body.keys()) == expected
