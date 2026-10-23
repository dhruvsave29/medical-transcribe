#!/usr/bin/env bash
# MediScript one-command dev setup (Linux/macOS).
# Creates .env from .env.example when missing, installs dependencies,
# ensures Ollama is present (local LLM only — never a cloud fallback),
# and starts the FastAPI backend (port 8000) + Vite frontend (port 5173).

set -euo pipefail
cd "$(dirname "$0")"

log() { printf '[MediScript] %s\n' "$*"; }

# ---- 1. .env ----
if [ ! -f .env ]; then
  cp .env.example .env
  log ".env created from .env.example"
fi
set -a; # shellcheck disable=SC1091
source .env 2>/dev/null
set +a
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# ---- 2. Ollama (local LLM) ----
if ! command -v ollama >/dev/null 2>&1; then
  log "Ollama not found. Attempting automatic install (one-time internet download)…"
  if command -v curl >/dev/null 2>&1 && curl -fsSL https://ollama.com/install.sh | sh; then
    log "Ollama installed."
  else
    log "AUTOMATIC INSTALL FAILED. Recovery command (run manually, may need admin):"
    log "  curl -fsSL https://ollama.com/install.sh | sh"
    log "Continuing without it — transcription still works; analysis/chat need Ollama."
  fi
fi
if command -v ollama >/dev/null 2>&1; then
  if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    log "Starting Ollama service…"
    (ollama serve >/dev/null 2>&1 &) || true
    sleep 3
  fi
  if ! ollama list 2>/dev/null | grep -q "${LLM_MODEL:-qwen2.5:3b}"; then
    log "Pulling local model ${LLM_MODEL:-qwen2.5:3b}…"
    ollama pull "${LLM_MODEL:-qwen2.5:3b}" || log "Model pull failed — run manually: ollama pull ${LLM_MODEL:-qwen2.5:3b}"
  fi
fi

# ---- 3. Python backend ----
if [ ! -f backend/.venv/bin/python ]; then
  log "Creating Python virtual environment…"
  python3 -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install --upgrade pip -q
backend/.venv/bin/python -m pip install -r backend/requirements.txt -q
log "Backend dependencies ready."

# ---- 4. Frontend deps ----
( cd frontend && npm install --no-fund --no-audit )

# ---- 5. Start servers ----
mkdir -p logs
log "Starting backend on port ${BACKEND_PORT}…"
( cd backend && exec .venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port "${BACKEND_PORT}" ) >> logs/backend.log 2>&1 &
BACK_PID=$!

log "Starting frontend on port ${FRONTEND_PORT}…"
( cd frontend && exec npm run dev ) >> logs/frontend.log 2>&1 &
FRONT_PID=$!

trap 'kill "$BACK_PID" "$FRONT_PID" 2>/dev/null; exit' INT TERM

log ""
log "MediScript is starting up:"
log "  App      -> http://localhost:${FRONTEND_PORT}"
log "  API      -> http://localhost:${BACKEND_PORT}"
log "  API docs -> http://localhost:${BACKEND_PORT}/api/docs"
log ""
log "First backend start downloads the Whisper model automatically."
log "Ctrl+C stops both servers."

wait
