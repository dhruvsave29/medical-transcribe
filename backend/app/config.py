from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

from functools import lru_cache


class Settings(BaseSettings):
    """All configuration comes from the root .env file (see .env.example).

    No cloud services and no API keys: ASR and LLM run on the local machine.
    """

    whisper_model: str = "small.en"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_cpu_threads: int = 4
    whisper_beam_size: int = 5

    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "qwen2.5:3b"
    llm_api_key: str = "local"
    llm_timeout_s: int = 180

    backend_port: int = 8000
    frontend_port: int = 5173

    max_upload_mb: int = 25

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
