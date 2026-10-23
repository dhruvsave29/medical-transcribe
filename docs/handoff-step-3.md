# Step 3 — Handoff: ASR backend + live transcript

Status: ✅ done, committed. Next: Step 4 (LLM analyzer `/api/analyze` with Ollama).

## What was built

- `backend/app/asr.py` — `Transcriber` interface + `FasterWhisperTranscriber`:
  faster-whisper `small.en`, CPU `int8`, `cpu_threads=4`, `beam_size=5` (all
  configurable via `.env`: `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`,
  `WHISPER_CPU_THREADS`, `WHISPER_BEAM_SIZE`). Audio decoded with
  `faster_whisper.audio.decode_audio` from the uploaded bytes (any container/rate
  ffmpeg/av can open, resampled to 16 kHz). English models force `language="en"`.
- Background preload (lifespan → `maybe_autoload()`): the model downloads/loads on
  backend start (guarded by `MEDISCRIPT_ASR_AUTOLOAD`, set to `0` by the test
  conftest so tests never touch the network). If a request arrives before preload
  finishes, the load happens inline.
- `POST /api/transcribe` per PRD 3.2: multipart `audio` + `chunk_index` + optional
  `language` → `{"chunk_index", "text", "duration_ms"}`. Errors: 400 empty upload,
  413 over `MAX_UPLOAD_MB`, 415 undecodable audio, 503 model/runtime failure — all in
  the global error contract. `GET /api/health` now reports real `model_ready`.
- Logging discipline (PRD 3.4): `mediscript.asr` logs only chunk duration, inference
  wall time and character counts — never transcript text.
- `frontend/src/lib/api.ts` — typed `transcribeChunk()` fetch wrapper with the
  PRD error contract mapped into `ApiError`.
- `frontend/src/lib/chunkUploader.ts` — serial upload queue: transcript order always
  matches chunk order; failed chunk → error toast with a **Retry** action that
  re-posts the held WAV; drained queue while recording flips the live strip back to
  "Listening…".
- `frontend/src/store/sessionStore.ts` — `appendTranscript()`; WORDS chip counts
  from the live transcript (already wired in Step 1).
- Save Recording now also downloads the transcript `.txt` whenever any text exists.

## How to run it right now

```
run.bat          (Windows)  /  run.sh  — or manual:
backend:  uvicorn app.main:app --port 8000      # model preloads in background
frontend: npm run dev                            # port 5173, /api proxied
```
Click Start Mic and speak — each VAD segment appears as text within seconds
(measured: ~3.5–3.8 s inference for 3–7 s chunks on this machine, int8 CPU).

## How it was verified (all green)

- `backend`: 10 pytest tests (health contract incl. `model_ready`, transcribe
  contract w/ deterministic stub, 400/413/415/422/503 error shapes).
- `docs/smoke_transcribe.py`: real model, real fixture audio →
  `"This is a test of the medical transcription system. The patient reports chest
  heaviness for three months…"`.
- `docs/verify_step3_transcribe.py` (Playwright, fake mic + TTS fixture):
  transcript boxes fill live as VAD chunks close, WORDS chip = transcript word
  count, uploader drains to 0, screenshot `docs/step3-live-transcript.png`.
- `docs/verify_step2_recorder.py` re-run: still fully green (no recorder
  regressions).
- Backend logs after a full session: only `duration=/took=/chars=` lines.
- `npm run build` (incl. `tsc -b`) clean.

## Known gaps (planned, not bugs)

- `/api/analyze` and `/api/chat` still Step 4/5; CTA + demo toggle unchanged.
- The interim "Transcribing…" strip can only be seen for a moment; chunk inference
  latency is ~1.0× real-time on CPU.

## Gotchas for the next session

- `av` must stay `<16` (`av==15`): faster-whisper 1.2.1 calls
  `av.open(..., metadata_errors=...)`, removed in av 19 — pin kept in
  `backend/requirements.txt`.
- resolve the transcriber via `asr_state.transcriber`, never `from asr_state
  import transcriber` at another import site: test stubs swap `asr_state.transcriber`
  dynamically (main.py does this correctly).
- Whisper preloads in the background at startup; the E2E will hit a 503 if it
  clicks before loading finishes — wait for `model_ready` (`/api/health`) in
  scripts that exercise transcription right after boot.
