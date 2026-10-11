"""Application configuration.

Settings are read from environment variables so the same code runs in
development, tests, and (later) production without edits. Every value has a
sensible development default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

DEFAULT_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
# Development-only placeholder secret. Production must set NOTENEST_SECRET_KEY.
DEFAULT_SECRET_KEY = "dev-insecure-secret-change-me-please-32b"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration."""

    app_name: str
    api_prefix: str
    database_url: str
    upload_dir: Path
    max_upload_size: int
    cors_origins: tuple[str, ...]
    secret_key: str
    access_token_ttl: int
    cookie_name: str
    cookie_secure: bool
    cookie_samesite: str
    seed_on_startup: bool


def _default_database_url() -> str:
    return f"sqlite:///{(BACKEND_DIR / 'notenest.db').as_posix()}"


def _parse_origins(value: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    """Build settings once from the environment.

    ``lru_cache`` keeps a single instance per process. Tests clear the cache
    and set the environment before importing, so they never touch the
    development database.
    """

    return Settings(
        app_name="NoteNest API",
        api_prefix="/api/v1",
        database_url=os.getenv("NOTENEST_DATABASE_URL", _default_database_url()),
        upload_dir=Path(
            os.getenv("NOTENEST_UPLOAD_DIR", str(BACKEND_DIR / "uploads"))
        ),
        max_upload_size=int(
            os.getenv("NOTENEST_MAX_UPLOAD_SIZE", str(DEFAULT_MAX_UPLOAD_SIZE))
        ),
        cors_origins=_parse_origins(
            os.getenv("NOTENEST_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
        ),
        secret_key=os.getenv("NOTENEST_SECRET_KEY", DEFAULT_SECRET_KEY),
        access_token_ttl=int(
            os.getenv("NOTENEST_ACCESS_TOKEN_TTL", str(60 * 60 * 24))
        ),
        cookie_name=os.getenv("NOTENEST_COOKIE_NAME", "notenest_session"),
        cookie_secure=_env_bool("NOTENEST_COOKIE_SECURE", False),
        cookie_samesite=os.getenv("NOTENEST_COOKIE_SAMESITE", "lax"),
        seed_on_startup=_env_bool("NOTENEST_SEED_ON_STARTUP", False),
    )
