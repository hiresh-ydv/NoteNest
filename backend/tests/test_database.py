"""Database initialization and isolation tests."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.config import BACKEND_DIR, get_settings
from app.database import engine, init_db


def test_init_db_creates_notes_table() -> None:
    init_db()

    assert "notes" in inspect(engine).get_table_names()


def test_sqlite_foreign_keys_enabled() -> None:
    with engine.connect() as connection:
        value = connection.execute(text("PRAGMA foreign_keys")).scalar()

    assert value == 1


def test_tests_use_an_isolated_database() -> None:
    settings = get_settings()
    development_url = f"sqlite:///{(BACKEND_DIR / 'notenest.db').as_posix()}"

    assert settings.database_url != development_url
    assert "notenest-tests-" in settings.database_url
    assert "notenest-tests-" in str(settings.upload_dir)
