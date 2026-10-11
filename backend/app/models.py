"""SQLAlchemy ORM models.

The MVP has a single table, ``notes``. PDF bytes are never stored here; only
metadata and a server-generated ``stored_filename`` that points at a file on
disk (file handling arrives in a later phase).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Note(Base):
    """A published academic note."""

    __tablename__ = "notes"
    __table_args__ = (
        CheckConstraint(
            "academic_year BETWEEN 1 AND 4",
            name="ck_notes_academic_year_range",
        ),
        CheckConstraint(
            "semester BETWEEN 1 AND 8",
            name="ck_notes_semester_range",
        ),
        CheckConstraint("file_size > 0", name="ck_notes_file_size_positive"),
        CheckConstraint(
            "download_count >= 0", name="ck_notes_download_count_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    topic: Mapped[str | None] = mapped_column(String(150), nullable=True)

    file_original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    download_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Note(id={self.id!r}, title={self.title!r}, subject={self.subject!r})"


class User(Base):
    """A registered account.

    Passwords are only ever stored as a salted hash. The email is stored
    normalized (lower-cased, trimmed) so uniqueness is case-insensitive.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Email-verification OTP. The code itself is never stored, only its hash.
    otp_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    otp_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    otp_last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"User(id={self.id!r}, email={self.email!r})"
