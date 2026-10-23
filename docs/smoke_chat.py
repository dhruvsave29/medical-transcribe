"""Real /api/chat smoke against local Ollama."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

TRANSCRIPT = (
    "The patient reports chest heaviness for three months, worse while climbing "
    "stairs, and gets relief at rest. The doctor recommends an ECG, some blood "
    "work, and aspirin 75 mg once daily. Follow-up in two weeks."
)

client = TestClient(app)
t0 = time.monotonic()
res = client.post(
    "/api/chat",
    json={"transcript": TRANSCRIPT, "summary": None, "message": "What medication was prescribed?"},
)
elapsed = round(time.monotonic() - t0, 1)
print("status:", res.status_code, "elapsed:", elapsed)
body = res.json()
print("reply:", body.get("reply", body))

t0 = time.monotonic()
res2 = client.post(
    "/api/chat",
    json={"transcript": TRANSCRIPT, "summary": None, "message": "Does the patient have a fever?"},
)
print("status:", res2.status_code, "elapsed:", round(time.monotonic() - t0, 1))
print("reply:", res2.json().get("reply", res2.json()))
