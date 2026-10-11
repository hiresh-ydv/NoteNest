"""Pytest configuration and shared fixtures.

The environment is redirected to a throwaway directory *before* the
application packages are imported, so every test runs against an isolated
SQLite database and never touches the development database.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

import support

_TMP_DIR = Path(tempfile.mkdtemp(prefix="notenest-tests-"))

os.environ["NOTENEST_DATABASE_URL"] = (
    f"sqlite:///{(_TMP_DIR / 'test.db').as_posix()}"
)
os.environ["NOTENEST_UPLOAD_DIR"] = str(_TMP_DIR / "uploads")
# Keep the oversized-upload test fast while the real default (10 MB) is
# asserted separately in the tests.
os.environ["NOTENEST_MAX_UPLOAD_SIZE"] = "2048"

# Application imports must come after the environment is set above.
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _isolated_environment() -> Iterator[None]:
    """Create the schema once, then clean up the whole temp directory."""

    init_db()
    yield
    engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def _fake_email(monkeypatch) -> None:
    """Capture OTP codes instead of sending real mail (no network at all)."""

    support.OUTBOX.clear()
    monkeypatch.setattr("app.routers.auth.email_service.send_otp_email", support.fake_send_otp_email)
    yield
    support.OUTBOX.clear()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """TestClient running the app lifespan (which calls init_db)."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def session() -> Iterator[Session]:
    """A clean schema and session per test."""

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def upload_dir() -> Iterator[Path]:
    """An empty, isolated upload directory for the duration of one test."""

    path = get_settings().upload_dir
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
