"""Real end-to-end ASR smoke test: fixture speech -> /api/transcribe text."""
import io
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

FIXTURE = Path(__file__).parent / "speech-then-10s-silence.wav"
client = TestClient(app)

with wave.open(str(FIXTURE), "rb") as w:
    rate, width, frames = w.getframerate(), w.getsampwidth(), w.getnframes()
    # first 14 s: pure speech, no silence tail
    seg = w.readframes(int(14 * rate))

buf = io.BytesIO()
with wave.open(buf, "wb") as w2:
    w2.setnchannels(1)
    w2.setsampwidth(width)
    w2.setframerate(rate)
    w2.writeframes(seg)

import time
t0 = time.monotonic()
res = client.post(
    "/api/transcribe",
    files={"audio": ("chunk.wav", buf.getvalue(), "audio/wav")},
    data={"chunk_index": "0"},
)
print("status:", res.status_code, "elapsed:", round(time.monotonic() - t0, 1))
print(res.json())