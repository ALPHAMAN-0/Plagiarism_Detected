"""
Application configuration loaded from environment variables.

No secrets should ever be hard-coded here. Use .env (gitignored) for local
overrides and real environment variables in production.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App metadata
    app_name: str = "Plagiarism_Detected"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS — explicit allowlist, never "*" in production
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # Storage paths (resolved to absolute paths at validation time)
    uploads_dir: Path = Path("./data/uploads")
    indexes_dir: Path = Path("./data/indexes")
    ml_models_dir: Path = Path("./app/ml_models")
    db_url: str = "sqlite+aiosqlite:///./data/plagiarism.db"

    # Upload limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_mime_prefixes: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
    )
    allowed_extensions: list[str] = Field(
        default_factory=lambda: ["pdf", "txt", "docx"]
    )

    # Auth (optional)
    api_key: str | None = None

    # Rate limits
    rate_limit_per_minute: int = 60
    upload_rate_limit_per_hour: int = 10

    # Model paths
    ai_classifier_path: Path = Path("./app/ml_models/ai_classifier.joblib")
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    perplexity_model_name: str = "distilgpt2"

    # Algorithm defaults
    default_ngram_size: int = 5
    default_top_k_matches: int = 5
    default_similarity_threshold: float = 0.6

    @field_validator("uploads_dir", "indexes_dir", "ml_models_dir", mode="after")
    @classmethod
    def _ensure_dir(cls, v: Path) -> Path:
        """Create the directory if it doesn't exist (idempotent)."""
        v.mkdir(parents=True, exist_ok=True)
        return v.resolve()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the LRU cache — useful in tests that override env vars."""
    get_settings.cache_clear()
