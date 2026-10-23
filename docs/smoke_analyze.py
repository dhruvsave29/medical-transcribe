"""Real end-to-end analyzer smoke: transcript -> /api/analyze -> validated schema."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.summary import ClinicalSummary

TRANSCRIPT = (
    "This is a test of the medical transcription system. The patient reports "
    "chest heaviness for three months, worse while climbing stairs. The doctor "
    "recommends an ECG, some blood work, and aspirin 75 mg once daily. The "
    "patient has no known drug allergies and no history of diabetes or "
    "hypertension. Follow-up in two weeks."
)

client = TestClient(app)
t0 = time.monotonic()
res = client.post(
    "/api/analyze",
    json={"transcript": TRANSCRIPT},
)
elapsed = round(time.monotonic() - t0, 1)
print("status:", res.status_code, "elapsed:", elapsed)
if res.status_code != 200:
    print(res.text[:400])
    sys.exit(1)
body = res.json()
print(json.dumps(body, indent=1)[:1600])

# validate against the same schema the endpoint used (double check)
ClinicalSummary.model_validate(body)
print("schema validated OK")
