# Hand-off — Step 1: Foundation, Design System and Static UI Shell

Date: 2026-10-23 · Duration of verification: installed + ran everything for real.

## What was built

- **Monorepo**: `/frontend` (Vite 7 + React 19 + TypeScript + Zustand 5), `/backend`
  (FastAPI + Pydantic v2 + pydantic-settings, Python 3.13 host satisfied "3.11+"),
  `/docs`. Fixed repo structure per PRD 3.4.
- **Backend**: `GET /api/health` → `{status, asr, llm, model_ready}` (model_ready stays
  `false` until Step 3 loads Whisper at startup). Global error contract
  `{"error":{"code","message"}}` enforced via handlers for both FastAPI and Starlette
  HTTP exceptions + validation errors. CORS restricted to the frontend origin.
- **Design tokens**: CSS variables in `src/styles/tokens.css` (accent #6366F1 indigo,
  red/green semantic, greys, radii 24px cards / pills, shadow scale, spacing scale,
  Inter font stack with system fallback — no CDN dependency at runtime besides the
  optional Google Fonts stylesheet).
- **Static UI per PRD Section 2** (all present and verified):
  - AppShell: thin top bar (brand left; Demo data toggle [dev only] + local-services
    status pill + hospital/demo name in accent, top right).
  - TranscriptionCard: 4 pill buttons (Start Mic filled indigo / Stop red outline /
    Clear grey outline / Save Recording green outline), WORDS + CHUNKS chips, live
    strip ("Listening…" animated dot), transcript area with the exact placeholder
    text and magic-wand icon, full-width "Process Transcript with AI" CTA with zap icon.
  - SummaryCard: hourglass title icon, right-aligned ✕ Clear, patient header with
    divider, scrollable body with 9 icon+uppercase-label+divider sections and the PRD's
    exact empty-state texts, resizable editable clinical summary textarea, sticky
    Copy to Prescription, custom thin scrollbar.
  - FloatingChatButton opening a drawer shell (activated fully in Step 5), Toaster with
    kind colours, optional action buttons and auto-dismiss.
- **State**: Zustand store with `idle | recording | stopped | processing` states, button
  enable/disable rules from PRD 2.4, left Clear double-click confirm, right Clear wipes
  summary only. WORDS counts live from transcript text.
- **Types**: `ClinicalSummary` interface mirrors PRD 3.3 exactly (+ `emptySummary()`).
- **Mock data**: fictional sample consultation + matching filled summary behind the
  dev-only **Demo data** top-bar toggle (only rendered in `import.meta.env.DEV`
  builds). Toggling off performs a clean session reset.
- **Copy to Prescription**: real formatter (`src/lib/prescription.ts`) → clipboard, with
  "Copied" toast; verified clipboard content starts `PATIENT: Ramesh Gupta` (2,171 chars).
- **Run scripts**: `run.bat` (Windows) and `run.sh` (Linux/macOS) create `.env` from
  `.env.example` automatically, create the Python venv, install deps, detect / install /
  start Ollama, and pull `qwen2.5:3b` — printing exact recovery commands
  (`winget install --id Ollama.Ollama -e ...` / `curl -fsSL https://ollama.com/install.sh | sh`)
  when an automatic install is blocked, then continuing (per PRD 1.1 the app must not
  silently ship broken; transcription-only operation remains valid until Step 4 wires
  the LLM).
- **AGENTS.md** at repo root contains PRD Sections 1–3 verbatim; README covers setup,
  env vars, API contracts and build status.

## How to run

```text
Windows:  run.bat          (repo root — starts backend 8000 + frontend 5173, opens browser)
Linux:    ./run.sh
Check:    curl http://localhost:8000/api/health  → {"status":"ok", ...}
App:      http://localhost:5173   |   API docs: http://localhost:8000/api/docs
```

## Verification performed (real runs)

- Backend: `pytest backend/tests` → 2 passed (health contract + error contract for
  unknown routes; the second test caught a real bug — Starlette 404s bypassing the
  error shape — now fixed).
- `curl /api/health` → `{"status":"ok","asr":"faster-whisper/small.en","llm":"ollama/qwen2.5:3b","model_ready":false}`.
- Frontend: `npm run typecheck` (tsc -b, strict) → 0 errors; dev server serves the app
  and `/api` proxy confirmed through the 5173 origin.
- Playwright/Chromium acceptance (27 assertions all passing, script kept at
  `docs/verify_step1_ui.py`):
  - exact card titles, 8 initial empty states, both CTA/Copy disabled while idle,
    WORDS: 0;
  - Start Mic → Recording… + pulsing + live strip + Stop enabled → Stop → back;
  - demo toggle → WORDS: 234, patient header "Ramesh Gupta", 461-char editable
    summary, 2 medication rows, "Denied by patient" split present;
  - clipboard copy verified; mock-off resets counts to 0;
  - no horizontal scroll at 1440 / 800 / 360 px; cards stack (transcription first) at
    360 px; screenshots saved as `docs/step1-desktop-mock.png`, `docs/step1-mobile.png`.

## Acceptance criteria (PRD Step 1) — all met

- Visual match to the screenshots: layout, colours, pill buttons, labelled sections
  with dividers, empty states, sticky footer. ✅
- 360–1440 px with no horizontal scroll. ✅
- Keyboard accessible: every interactive element is a real <button> with aria-label /
  aria-pressed / visible focus rings (`:focus-visible`, 2px indigo). ✅
- Mock data renders every section correctly. ✅

## Known gaps / notes for Step 2+ agents

1. `Save Recording` and the chat drawer input are intentionally inert; both show
   explanatory states and are scheduled for Step 2/5 (per plan).
2. `/api/analyze` is not implemented: the CTA performs the real fetch, handles the 404
   gracefully with a toast + "Preview demo" action, and already implements the full
   success/error/retry path — Step 4's endpoint will be picked up transparently.
3. `model_ready` in `/api/health` is always `false` until Step 3.
4. Inter font loads from Google Fonts with a full system-font fallback stack; if the
   machine is offline the design remains intact.
5. Vite dev uses strictPort — anything already bound to 5173 must be closed first.
6. Bootstrap chrome: `npm install` shows an npm funding notice; dev-time only, ignored.
7. Environment: Python 3.13.5, Node 22.12, npm 11.12 on Windows 10/11; Ollama not
   installed yet — run.bat installs it (winget) or prints the recovery command.
