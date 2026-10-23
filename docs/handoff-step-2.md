# Step 2 — Handoff: Mic capture + Silero VAD chunking

Status: ✅ done, committed. Next: Step 3 (ASR backend, faster-whisper `small.en`).

## What was built

- `frontend/src/audio/recorder.ts` — `RecorderService` (`start/stop/saveSession/`
  `clearSession`), mic `MicVAD` from `@ricky0123/vad-web` 0.0.31 (`model: 'v5'`),
  per-session PCM collection, VAD speech-end → 16 kHz mono PCM-16 WAV chunk,
  `chunkCount`, dev-only `window.__mediscript.recorder` handle.
- `frontend/src/audio/vadConfig.ts` — VAD/ORT config: thresholds positive 0.45 /
  negative 0.32, redemption 700 ms, pre-speech pad 500 ms, min speech 400 ms,
  `frameSamples` 512; local asset paths (`/vad/` + per-mode ORT wasmPaths) and
  `ortConfig.numThreads = 1` (no COOP/COEP needed).
- `frontend/src/audio/wav.ts` — PCM-16 WAV encoder (AudioBuffer→16k mono WAV).
- `frontend/src/hooks/useRecorder.ts` — React wiring: start/stop/save/clear, event
  → store (`recordChunk`, `recorderFailure`, statuses), toast mapping per error kind
  (permission denied → precise message; other mic failures → generic message with
  Retry), `Save Recording` downloads session WAV (and transcript `.txt` only when
  text exists).
- `frontend/src/components/RecorderDebugPanel.tsx` — dev-only event feed mirroring
  recorder events (used by the E2E to assert debug rows == chunk count).
- `frontend/scripts/copy-vad-assets.mjs` + `vite.config.ts` trampolined
  `predev`/`prebuild` npm scripts: copies Silero ONNX + worklet → `public/vad/`,
  ORT wasm/mjs → BOTH `src/vendor/` (dev) and `public/vad/ort/` (build). All
  generated asset dirs are git-ignored; the app never touches a CDN for VAD/ORT.
- `frontend/src/styles/app.css` — recording badge, live strip states, chips,
  clear-confirm, debug panel styling.
- `docs/speech-then-10s-silence.wav` — generated fixture (TTS speech 16.5 s +
  10 s silence) used as a looping fake microphone capture.

## How to run it right now

```
# from repo root
python backend\run.py          # or: .venv\Scripts\python -m uvicorn app.main:app --port 8000
npm run dev                    # in frontend\  (predev copies VAD assets automatically)
```
Open http://localhost:5173, click **Start Mic** (needs Chrome/Edge), grant mic.

## How it was verified (all green)

`python docs\verify_step2_recorder.py` drives a real Chromium with Windows fake-audio
file capture (the fixture) through 24 assertions:

- first VAD chunk appears (silero inference on, single-thread WASM, local assets)
- 4 speech chunks over 30 s with a 13.6 s pure-silence gap that produced **zero**
  chunks (silence and noise filtered exactly as the PRD requires)
- `WORDS`/`CHUNKS` chips update live; debug panel rows match chunk events
- Save after stop downloads a valid 16 000 Hz / mono / 16-bit WAV (30.8 s)
- mic tracks end on Stop **and** after Clear; restart recording works; Clear
  wipes counters (aria-labelled double-press confirm)
- zero requests to any CDN host during inference
- a browser denied media access shows the precise error toast with Retry and the
  app stays usable (headless Playwright denies via `NotSupportedError`; real
  browsers hit `NotAllowedError`, mapped to the permission message)

Also `npm run build` (includes `tsc -b`) passes; warnings reduced to the single
bundle-size note (ORT wasm loader); nothing else in shipped code has TODOs.

## Known gaps (planned, not bugs)

- Transcript box still shows interim "Listening…" only — text arrives with Step 3.
- Save Recording downloads the raw session audio; per-chunk upload → `/api/transcribe`
  is Step 3's wiring.
- Mock "Demo data" toggle unchanged (that's the Step 1 dev tool).

## Gotchas for the next session

- ORT 1.30 overrides `wasmPaths` via object form; if you change paths, keep BOTH the
  `src/vendor` copy (dev) and `public/vad/ort` copy (build) — `copy-vad-assets.mjs`
  handles it.
- Fake-audio capture path in Playwright args must NOT be quoted, or Chromium falls
  back to a sine tone and VAD never fires (cost an hour of debugging).
- `useRecorder` must click `Stop` before `Save Recording` — Save is disabled while
  the session is live (UI rule from the PRD state machine).
