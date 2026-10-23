# Changelog

All notable changes per build step. Contracts in the PRD (AGENTS.md sections 1–3) must not
change without an entry here.

## [0.1.0] — Step 1 — 2026-10-23

### Added
- Monorepo scaffold: `/frontend` (Vite + React 19 + TypeScript + Zustand), `/backend`
  (FastAPI + Pydantic v2 + pydantic-settings), `/docs`.
- Backend `GET /api/health` contract-ready, plus the global error shape
  `{"error": {"code", "message"}}` via HTTPException/Validation handlers.
- Design tokens as CSS variables (accent #6366F1 indigo, semantic red/green/grey, radii,
  shadows, spacing scale, Inter font stack).
- Static UI shell per PRD Section 2: AppShell (top bar), TranscriptionCard (Start Mic /
  Stop / Clear / Save Recording pills, WORDS/CHUNKS chips, live strip, transcript area,
  CTA), SummaryCard (patient header, 9 labelled sections with dividers + empty states,
  editable clinical summary textarea, sticky Copy to Prescription), FloatingChatButton
  (drawer shell), Toaster.
- Zustand session store with states idle/recording/stopped/processing + toast system.
- `ClinicalSummary` TypeScript interface mirroring PRD 3.3, with `emptySummary()`.
- Plain-text "Copy to Prescription" formatter (`src/lib/prescription.ts`), wired to
  clipboard with success/error toasts.
- Dev-only "Demo data" toggle (top bar, dev builds only) with fictional sample
  consultation transcript + filled `ClinicalSummary` so every UI state is reviewable.
- `run.sh` and `run.bat`: auto-create `.env`, create the Python venv, install deps,
  check/install/start Ollama (with copy-pasteable recovery commands when blocked), pull
  `qwen2.5:3b`, and start both servers.
- `.env.example` with every PRD 1.1 variable; `.gitignore`; README; AGENTS.md with PRD
  sections 1–3; backend smoke tests (`backend/tests/test_health.py`).

## [0.2.0] — Step 2 — 2026-10-24

### Added
- Real microphone capture: `getUserMedia` + `@ricky0123/vad-web` (Silero v5) behind
  `RecorderService` (`frontend/src/audio/recorder.ts`) using mic `MicVAD` with
  `pauseStream/resumeStream` between segments.
- VAD tuning per PRD intent in `vadConfig.ts`: positive 0.45 / negative 0.32,
  redemption 700 ms, pre-speech padding 500 ms, minimum speech 400 ms — so short noise
  blips never reach ASR but natural sentence pauses do close chunks fast.
- Automatic chunking: every VAD speech-end closes a 16 kHz / mono / PCM-16 WAV in
  `wav.ts` (worklet ring buffer collecting per-session PCM, chunked on VAD speech-end,
  downsampled once from the browser's 48 kHz stream), exposes `chunkCount`,
  `saveSession()` (full-session blob) and a `useRecorder` hook wiring events into the
  Zustand store.
- **No-CDN guarantee:** `frontend/scripts/copy-vad-assets.mjs` (wired as vite
  `predev`/`prebuild`) copies Silero ONNX + worklet + ORT wasm/mjs into
  `frontend/public/vad/` and `frontend/src/vendor/`, git-ignored; `vadConfig.ts` points
  `baseAssetPath`/`onnxWASMBasePath` at `/vad/` and overrides ORT `wasmPaths` per
  dev/build for single-threaded WASM (no COOP/COEP needed).
- Recording UI state machine (`useRecorder` hook + store events): Start Mic disabled +
  pulsing badge while recording, Stop releases the mic tracks, Clear wipes counters
  (confirm when transcript exists, aria-labelled), Save Recording downloads the
  16 kHz mono session WAV and the transcript `.txt` only when text exists.
- Error handling per PRD: microphone failures map to user-kind messages (permission
  denied → precision message, not-supported/unknown → generic mic message), toasts carry
  a Retry action and the app stays usable after denial.
- Dev-only `RecorderDebugPanel` (dev builds only): live event feed mirroring every
  recorder event for acceptance verification.
- `docs/verify_step2_recorder.py`: full Playwright E2E with Chromium's real
  fake-audio-capture fixture (TTS speech + 10 s silence) — 24 assertions, all passing;
  `docs/diag_*.py` focused diagnostics; test fixture generation embedded in the script.

### Fixed
- Starlette 0.x default 404 body didn't match the PRD error contract; now all unhandled
  paths and validation errors return `{"error": {code, message}}`.
- ORT 1.30 asset resolution: `.mjs` loader path override so inference threads never
  touch a CDN in dev or build.

### Known gaps (by plan)
- ASR backend (`/api/transcribe`), live transcript text, WORDS counter and CTA wiring
  arrive in Step 3 (`backend/asr.py` faster-whisper small.en int8).
- Chat drawer and AI analysis remain Step 4/5; mock data still behind the dev toggle.

**Run:** `run.bat` (Windows) → http://localhost:5173 (frontend) · http://localhost:8000
reads `/api/health` (backend). Vite dev server on 5173 proxies `/api` to 8000.
