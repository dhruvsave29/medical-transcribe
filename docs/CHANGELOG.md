# Changelog

All notable changes per build step. Contracts in the PRD (AGENTS.md sections 1–3) must not
change without an entry here.

## [1.0.0] — Step 6 — 2026-10-24

### Final assembly (cold-start verified)
- **Cold-start test passed**: wiped `.venv`, `node_modules` and `.env`, ran
  `run.bat` from scratch — `.env` created, venv + deps installed, Ollama
  checked, servers launched, Whisper preloaded (`model_ready: true`), app live
  at :5173, then the full verification battery re-run green.
- `run.bat` fixed: Ollama resolved through PATH *plus* the two known install
  locations (a fresh winget install leaves PATH stale in the current shell, so
  the old script silently skipped the model pull); single idempotent
  `npm install`; explicit `goto backend_setup` flow.
- `backend/requirements-dev.txt` added (pytest + httpx) so a fresh machine can
  run the 24-test backend suite; documented in the README.
- README updated: full config table, real API contracts, build-status table,
  verification assets.
- Sweep: no TODOs, no dead buttons, no placeholder logic in shipped code; every
  PRD 2.x control demonstrated working in E2E.
- Final screenshots: `docs/final-desktop.png`, `docs/final-mobile.png`.
- Earlier steps' verification is recorded in `docs/handoff-step-*.md`; suites:
  `docs/verify_step{2,3,4,5}_*.py`, smokes `docs/smoke_{transcribe,analyze,chat}.py`.

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

### [0.3.0] — Step 3 — 2026-10-24

### Added
- `POST /api/transcribe` behind the `Transcriber` interface: faster-whisper
  `small.en` (int8, CPU, 4 threads, beam 5) — all tunable via `.env`. Uploaded
  chunk audio decodes through `av` to 16 kHz float32; errors 400/413/415/422/503 in
  the PRD error contract. `GET /api/health` now flips `model_ready` to true once
  the model is loaded.
- Background ASR preload at backend startup (`MEDISCRIPT_ASR_AUTOLOAD`, disabled in
  tests); the model downloads once into the HuggingFace cache on first start.
- Live transcript flow: `frontend/src/lib/api.ts` (`transcribeChunk`) +
  `frontend/src/lib/chunkUploader.ts` — serial upload queue so transcript order
  matches chunk order, failure toasts with Retry, live strip flips
  "Listening… ⇄ Transcribing…", WORDS chip counts the growing transcript.
- Save Recording now also downloads the transcript `.txt` when text exists.
- Test suite grows to 10 backend tests (contract + error shapes with a
  deterministic stub transcriber); Playwright E2E for the live-transcript path
  (`docs/verify_step3_transcribe.py`) + real-inference smoke
  (`docs/smoke_transcribe.py`).

### Fixed
- Pinned `av>=11,<16` — faster-whisper 1.2.1 uses `av.open(metadata_errors=…)`,
  removed in av 19 (pip default), which broke chunk decoding with a 415.

## Known gaps (by plan)
- ASR chunk latency ~1.0× real-time on CPU int8 (fine for live dictation pace).
- GitHub export happens after Step 6 (user's flow).

## [0.5.0] — Step 5 — 2026-10-24

### Added
- `POST /api/chat` (PRD 3.2 contract): transcript+summary+message → `{"reply"}`,
  answered strictly from the transcript/summary with the enforced
  "does not contain" refusal; summary field validated as ClinicalSummary or null.
- `Analyzer.chat()` on the shared Ollama client (temp 0, grounded-only prompt).
- Real chat drawer replaces the Step-1 placeholder: bubbles, Thinking… state,
  Enter-to-send, clear-chat, disabled-with-hint until a transcript exists,
  error toasts with Retry.
- Shared typed API helpers (`chatWithAssistant`, `analyzeTranscript`) — CTA
  migrated off the ad-hoc fetch.
- 7 new backend tests (24 total) + chat smoke + Playwright E2E
  (`docs/verify_step5_chat.py`, screenshot `docs/step5-chat.png`).

**Run:** `run.bat`. All five steps now verified end-to-end with local inference.

## [0.4.0] — Step 4 — 2026-10-24

### Added
- `POST /api/analyze` behind the `Analyzer` interface: local Ollama
  (`qwen2.5:3b` via the OpenAI-compatible `/v1` client, `response_format=json_object`,
  temperature 0, one parse-retry), responses validated against the PRD 3.3
  `ClinicalSummary` Pydantic models before leaving the backend.
- Hostile-LLM coercion in `summary.py`: strings/None/dicts normalized into list
  fields, medication objects accepted, empty med names dropped — schema stays
  exact while models wobble.
- CTA processing state per PRD 2.4: spinner + "Analysing…" + disabled during
  inference (`.btn--busy` styles).
- `.env.example`/config: `WHISPER_CPU_THREADS`, `WHISPER_BEAM_SIZE`, `LLM_TIMEOUT_S`.
- 7 new backend tests (contract, 400/422/503, unreachable LLM, key whitelist);
  Playwright full-pipeline E2E (`docs/verify_step4_analyze.py`) and real-inference
  smoke (`docs/smoke_analyze.py`); screenshot `docs/step4-summary.png`.

### Fixed
- Environment missing Ollama: installed v0.40.9 via winget and pulled qwen2.5:3b;
  `run.bat` logic now exercises its real install path.

**Run:** `run.bat` (Windows). Note: first analyze after a cold boot takes ~15 s
(model warm-up in Ollama RAM); then ~5–12 s per summary.

**Run:** `run.bat` (Windows) → http://localhost:5173 (frontend) · http://localhost:8000
reads `/api/health` (backend). Vite dev server on 5173 proxies `/api` to 8000.

