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
