"""Environment-driven configuration for the Talent Match RAG pipeline.

Required variables: PINECONE_API_KEY, GROQ_API_KEY. The remaining
variables have defaults matching .env.example and TRD.md section 4.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing or invalid."""


def parse_origins(raw: str) -> list[str]:
    """Split a comma-separated origin list, discarding blank entries."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_cors_origins() -> list[str]:
    """Return the browser origins allowed to call the API.

    Resolved separately from get_settings so that importing the FastAPI app
    never depends on Pinecone or Groq credentials being present, which would
    otherwise make the app unimportable for local frontend work and would
    break the ability to read the OpenAPI schema.
    """
    load_dotenv()
    return parse_origins(os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS))



@dataclass(frozen=True)
class Settings:
    """Immutable settings resolved from the environment."""

    pinecone_api_key: str
    pinecone_index_name: str
    groq_api_key: str
    groq_model: str
    embedding_model: str
    top_k: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from the environment, raising ConfigError if required variables are missing."""
    load_dotenv()
    missing = [
        name for name in ("PINECONE_API_KEY", "GROQ_API_KEY") if not os.getenv(name)
    ]
    if missing:
        raise ConfigError(
            "Missing required environment variables: " + ", ".join(missing)
        )
    raw_top_k = os.getenv("TOP_K", "5")
    try:
        top_k = int(raw_top_k)
    except ValueError as exc:
        raise ConfigError(f"TOP_K must be an integer, got {raw_top_k!r}") from exc
    if top_k < 1:
        raise ConfigError(f"TOP_K must be >= 1, got {top_k}")
    return Settings(
        pinecone_api_key=os.environ["PINECONE_API_KEY"],
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "talent-match"),
        groq_api_key=os.environ["GROQ_API_KEY"],
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        top_k=top_k,
    )
