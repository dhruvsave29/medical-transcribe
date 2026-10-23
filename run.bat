@echo off
REM MediScript one-command dev setup (Windows).
REM Creates .env from .env.example when missing, installs dependencies,
REM ensures Ollama is present (local LLM only — never a cloud fallback),
REM and starts the FastAPI backend (port 8000) + Vite frontend (port 5173).

setlocal EnableExtensions
cd /d "%~dp0"

echo [MediScript] Step 1/5 - configuration
if not exist ".env" (
  copy /y ".env.example" ".env" >nul
  echo [MediScript] .env created from .env.example
)

set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "LLM_MODEL=qwen2.5:3b"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set "BACKEND_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
    if /i "%%A"=="LLM_MODEL" set "LLM_MODEL=%%B"
  )
)

echo [MediScript] Step 2/5 - Ollama (local LLM, no API key)
set "OLLAMA_EXE="
where ollama >nul 2>nul
if not errorlevel 1 set "OLLAMA_EXE=ollama"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_EXE if exist "C:\Program Files\Ollama\ollama.exe" set "OLLAMA_EXE=C:\Program Files\Ollama\ollama.exe"
if not defined OLLAMA_EXE (
  echo [MediScript] Ollama not found. Attempting silent install via winget...
  winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements >nul 2>nul
  if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
  if not defined OLLAMA_EXE if exist "C:\Program Files\Ollama\ollama.exe" set "OLLAMA_EXE=C:\Program Files\Ollama\ollama.exe"
)
if not defined OLLAMA_EXE (
  echo [MediScript] AUTOMATIC INSTALL FAILED. Recovery command ^(may ask for administrator approval^):
  echo     winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
  echo [MediScript] Continuing - transcription works; AI summary/chat need Ollama.
  goto backend_setup
)
curl -fsS http://127.0.0.1:11434/api/version >nul 2>nul
if errorlevel 1 (
  echo [MediScript] Starting Ollama service...
  start "Ollama service" /min cmd /c ""%OLLAMA_EXE%" serve >nul 2>nul"
  timeout /t 3 /nobreak >nul
)
"%OLLAMA_EXE%" list 2>nul | findstr /c:"%LLM_MODEL%" >nul
if errorlevel 1 (
  echo [MediScript] Pulling local model %LLM_MODEL% ^(one-time download^)...
  "%OLLAMA_EXE%" pull %LLM_MODEL%
  if errorlevel 1 echo [MediScript] Model pull failed - run manually: ollama pull %LLM_MODEL%
)

:backend_setup
echo [MediScript] Step 3/5 - Python backend
if not exist "backend\.venv\Scripts\python.exe" (
  echo [MediScript] Creating Python virtual environment...
  python -m venv "backend\.venv"
  if errorlevel 1 (
    echo [MediScript] venv creation failed. Recovery command:
    echo     python -m venv backend\.venv
    pause
    exit /b 1
  )
)
call "backend\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip -q
python -m pip install -r backend\requirements.txt -q
if errorlevel 1 (
  echo [MediScript] pip install failed - check internet access, then re-run this script.
  pause
  exit /b 1
)
echo [MediScript] Backend dependencies ready.

echo [MediScript] Step 4/5 - Frontend dependencies
pushd frontend
echo [MediScript] Installing npm dependencies (idempotent - instant if present)...
call npm install --no-fund --no-audit
if errorlevel 1 (
  echo [MediScript] npm install failed. Recovery command:
  echo     cd frontend ^&^& npm install
  popd
  pause
  exit /b 1
)
popd

echo [MediScript] Step 5/5 - Starting servers
start "MediScript backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "MediScript frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [MediScript] Starting up:
echo     App      -^> http://localhost:%FRONTEND_PORT%
echo     API      -^> http://localhost:%BACKEND_PORT%
echo     API docs -^> http://localhost:%BACKEND_PORT%/api/docs
echo.
echo [MediScript] First backend start downloads the Whisper model automatically.
echo [MediScript] Opening the app in your default browser...
timeout /t 4 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

endlocal
