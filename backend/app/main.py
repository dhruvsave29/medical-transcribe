"""MediScript backend entrypoint.

Step 3 of the build plan: /api/health + /api/transcribe (faster-whisper,
local CPU). Later steps add /api/analyze and /api/chat behind an Analyzer
interface.
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import analyzer_state, asr_state
from .analyzer import AnalyzerError
from .asr import TranscriberError, maybe_autoload
from .summary import ClinicalSummary
from .config import settings

# App-level logs (model load, per-request sizes/durations — never transcript text).
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Download/load the ASR model in the background on first backend start."""
    maybe_autoload()
    yield


app = FastAPI(
    title="MediScript API",
    version="0.3.0",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Every error answers with {"error": {"code", "message"}} per the API contract."""
    code = {
        400: "bad_request",
        404: "not_found",
        422: "validation_error",
        429: "rate_limited",
        503: "service_unavailable",
    }.get(exc.status_code, f"http_{exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {"error": {"code": code, "message": exc.detail or "Request failed."}}
        ),
    )


app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request payload: " + str(exc.errors()[0].get("msg", "invalid input")),
                }
            }
        ),
    )


@app.get("/api/health")
async def health() -> dict:
    """Liveness + configuration report.

    model_ready flips to true once the Whisper model has loaded (background
    preload or first /api/transcribe call).
    """
    return {
        "status": "ok",
        "asr": f"faster-whisper/{settings.whisper_model}",
        "llm": f"ollama/{settings.llm_model}",
        "model_ready": asr_state.transcriber.is_ready,
    }


@app.post("/api/transcribe")
async def transcribe(
    audio: Annotated[UploadFile, File()],
    chunk_index: Annotated[int, Form(ge=0)],
    language: Annotated[str | None, Form(max_length=8)] = None,
) -> dict:
    """One VAD speech segment in (16 kHz mono WAV from the browser), text out.

    Contract (PRD 3.2): {"chunk_index", "text", "duration_ms"}.
    """
    contents = await audio.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty audio upload.")
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Audio larger than {settings.max_upload_mb} MB.",
        )

    try:
        text, duration = asr_state.transcriber.transcribe(contents, language)
    except TranscriberError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except Exception as exc:  # model/runtime failure — retryable client-side
        raise HTTPException(
            status_code=503, detail="Transcription service unavailable."
        ) from exc

    return {
        "chunk_index": chunk_index,
        "text": text,
        "duration_ms": int(round(duration * 1000)),
    }


@app.post("/api/analyze")
async def analyze(request: Request) -> JSONResponse:
    """Full transcript in, validated ClinicalSummary out (PRD 3.2/3.3).

    Body: {"transcript": "..."} — the validated summary JSON is returned
    directly. Inference runs on the local Ollama daemon (qwen2.5:3b).
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body must be JSON.")
    if not isinstance(body, dict) or not isinstance(body.get("transcript"), str):
        raise HTTPException(
            status_code=422, detail="Field 'transcript' (string) is required."
        )
    transcript: str = body["transcript"].strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    try:
        summary = analyzer_state.analyzer.analyze(transcript)
    except AnalyzerError as exc:
        raise HTTPException(status_code=503, detail=str(exc) + " — retry.") from exc
    except Exception as exc:
        logger.error("analyze failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Local LLM unavailable — retry."
        ) from exc

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(summary.model_dump(mode="json")),
    )


@app.post("/api/chat")
async def chat(request: Request) -> dict:
    """Consultation assistant: answers only from the transcript + summary.

    Contract (PRD 3.2): {"transcript", "summary", "message"} -> {"reply"}.
    The summary field may be a validated ClinicalSummary object or null.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body must be JSON.")
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Body must be a JSON object.")
    if not isinstance(body.get("message"), str) or not body["message"].strip():
        raise HTTPException(
            status_code=422, detail="Field 'message' (non-empty string) is required."
        )
    message: str = body["message"].strip()
    if not isinstance(body.get("transcript"), str) or not body["transcript"].strip():
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    transcript: str = body["transcript"].strip()
    summary_json = ""
    if body.get("summary") is not None:
        try:
            summary = ClinicalSummary.model_validate(body["summary"])
        except Exception:
            raise HTTPException(
                status_code=422, detail="Field 'summary' does not match the ClinicalSummary schema."
            )
        summary_json = json.dumps(summary.model_dump(mode="json"), ensure_ascii=False)

    try:
        reply = analyzer_state.analyzer.chat(transcript, summary_json, message)
    except AnalyzerError as exc:
        raise HTTPException(status_code=503, detail=str(exc) + " — retry.") from exc
    except Exception as exc:
        logger.error("chat failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Local LLM chat unavailable — retry."
        ) from exc

    return {"reply": reply}
