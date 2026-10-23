"""MediScript backend entrypoint.

Step 1 of the build plan: FastAPI app with /api/health only.
Later steps add /api/transcribe, /api/analyze and /api/chat behind
Transcriber / Analyzer interfaces.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings

app = FastAPI(
    title="MediScript API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
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

    model_ready flips to true in Step 3 once the Whisper model has loaded.
    """
    return {
        "status": "ok",
        "asr": f"faster-whisper/{settings.whisper_model}",
        "llm": f"ollama/{settings.llm_model}",
        "model_ready": False,
    }
