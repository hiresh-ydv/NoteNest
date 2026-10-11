"""Database engine, session factory, and initialization.

Uses SQLAlchemy 2.x with a small, explicit surface:
- one engine built from settings,
- a session factory and a FastAPI dependency with safe cleanup,
- ``init_db`` which only ever creates missing tables (never drops).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Turn on SQLite foreign-key enforcement for every connection."""

    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session with safe lifecycle.

    The caller owns the transaction: route handlers commit explicitly. On an
    exception we roll back, and we always close the session.
    """

    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(bind: Engine | None = None) -> None:
    """Create missing tables and ensure the upload directory exists.

    ``Base.metadata.create_all`` is idempotent and never drops existing data,
    so it is safe to run on every startup.
    """

    # Importing models registers their tables on Base.metadata.
    from app import models  # noqa: F401

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=bind or engine)
