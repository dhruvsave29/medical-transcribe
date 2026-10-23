# MediScript — Live Medical Transcription & AI Clinical Summary

A web app that listens to a doctor–patient consultation through the microphone, filters
silence/noise with Voice Activity Detection (VAD), transcribes speech locally with
**faster-whisper** (OpenAI Whisper architecture), shows the transcript live, and — on session
end — sends the full transcript to a **local Ollama LLM** that extracts structured medical
information and produces a concise clinical summary.

**Everything runs on your machine.** No cloud LLM, no API key for AI features, no analytics,
no storage. Transcript text never leaves the device.

## Tech stack (locked in the PRD)

| Layer | Choice |
| --- | --- |
| Frontend | React + TypeScript + Vite + Zustand, plain CSS variables — port **5173** |
| Backend | Python 3.11+, FastAPI, Pydantic v2, Uvicorn — port **8000** |
| ASR | `faster-whisper` `small.en` on CPU (int8), model autodownloaded on first start |
| VAD | Silero VAD in the browser (`@ricky0123/vad-web`), assets served locally |
| LLM | Ollama OpenAI-compatible API (`http://127.0.0.1:11434/v1`), model `qwen2.5:3b` |

## Prerequisites

- Node.js 20.19+ / 22+
- Python 3.11+
- [Ollama](https://ollama.com) — installed automatically by the run scripts when possible
  (this may require one administrator approval on Windows)
- ~6 GB disk for models (Whisper `small.en` ≈ 460 MB, `qwen2.5:3b` ≈ 2 GB) and 8 GB+ RAM
  recommended

## Quick start

### Windows

```bat
run.bat
```

### Linux / macOS

```bash
./run.sh
```

The script: creates `.env` from `.env.example` (automatic), installs Python + npm
dependencies, checks/installs/starts Ollama, pulls `qwen2.5:3b`, then opens the app at
**http://localhost:5173** (API on http://localhost:8000, docs at `/api/docs`).

### Manual (if you prefer)

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt   # Windows
backend/.venv/bin/python -m pip install -r backend/requirements.txt       # Linux/macOS

cd frontend && npm install && npm run dev        # terminal 1
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000   # terminal 2
```

## Configuration (`.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHISPER_MODEL` | `small.en` | ASR model. Set `small` for non-English speech |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | CT2 quantisation |
| `WHISPER_CPU_THREADS` | `4` | CTranslate2 CPU threads |
| `WHISPER_BEAM_SIZE` | `5` | Beam width (lower = faster) |
| `LLM_BASE_URL` | `http://127.0.0.1:11434/v1` | Ollama OpenAI-compatible endpoint |
| `LLM_MODEL` | `qwen2.5:3b` | Local LLM used for analysis + chat |
| `LLM_API_KEY` | `local` | Optional placeholder; local Ollama ignores it |
| `LLM_TIMEOUT_S` | `180` | Per-request LLM timeout |
| `BACKEND_PORT` | `8000` | FastAPI port |
| `FRONTEND_PORT` | `5173` | Vite port |

## API (Vite proxies `/api` to the backend in dev)

| Endpoint | Contract |
| --- | --- |
| `GET /api/health` | `{ status, asr, llm, model_ready }` — `model_ready: true` once Whisper has loaded |
| `POST /api/transcribe` | multipart wav (16 kHz mono VAD chunk) → `{ chunk_index, text, duration_ms }` |
| `POST /api/analyze` | `{ transcript }` → validated `ClinicalSummary` JSON |
| `POST /api/chat` | `{ transcript, summary, message }` → `{ reply }` (answers only from the transcript/summary) |
| Errors | `{ "error": { "code": "...", "message": "..." } }` |

## Project structure

```
├── AGENTS.md            # PRD sections 1–3 loaded by all agents every session
├── run.sh / run.bat     # one-command autonomous setup + start
├── backend/             # FastAPI app (app/asr.py, app/analyzer.py, app/summary.py)
│   └── requirements-dev.txt   # pytest + httpx for the backend test suite
├── frontend/            # React + TS + Vite app (mic + VAD + uploader + UI)
├── docs/                # handoff notes per step + changelog + E2E scripts
└── .env.example         # every configuration variable, documented
```

## Build status

All six planned steps are complete and verified end-to-end with real local
inference:

| Step | Scope | Status |
| --- | --- | --- |
| 1 | Foundation, design system, static UI shell | ✅ |
| 2 | Mic capture + browser Silero VAD chunking (no CDN) | ✅ |
| 3 | faster-whisper ASR + live in-order transcript | ✅ |
| 4 | Ollama analysis → validated ClinicalSummary | ✅ |
| 5 | Floating chat drawer + grounded /api/chat | ✅ |
| 6 | Cold-start assembly, docs, final sweep | ✅ |

Verification assets (run with any dev server up):
`docs/verify_step2_recorder.py`, `docs/verify_step3_transcribe.py`,
`docs/verify_step4_analyze.py`, `docs/verify_step5_chat.py`, plus
`backend/tests` (24 tests; needs `backend/requirements-dev.txt`).

## Important notes

- **AI disclaimer:** the summary is AI-generated and must be reviewed by a clinician
  before use in any medical record.
- **Privacy:** transcripts are treated as sensitive data; nothing is stored by default and
  no transcript text is logged.
- Dev builds expose a **Demo data** toggle (top bar) that fills the UI with a fictional
  sample consultation so every UI state can be reviewed. It never ships in production
  builds.
