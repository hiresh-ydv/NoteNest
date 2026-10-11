"""Note listing and detail endpoints.

Query building is factored into small helpers so the route handlers stay
focused on request/response concerns. All filtering uses SQLite-compatible
SQLAlchemy expressions (no external search infrastructure).
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import Note, User
from app.routers.auth import get_current_user
from app.schemas import NoteListResponse, NoteRead
from app.services import files

router = APIRouter(prefix="/notes", tags=["notes"])

settings = get_settings()


def _escape_like(term: str) -> str:
    """Escape LIKE wildcards so user input matches literally."""

    return (
        term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )


def _apply_filters(
    stmt: Select,
    *,
    query: str | None,
    subject: str | None,
    academic_year: int | None,
    semester: int | None,
) -> Select:
    """Apply keyword search and exact filters with AND semantics."""

    if query and query.strip():
        pattern = f"%{_escape_like(query.strip())}%"
        stmt = stmt.where(
            or_(
                Note.title.ilike(pattern, escape="\\"),
                Note.description.ilike(pattern, escape="\\"),
                Note.subject.ilike(pattern, escape="\\"),
                Note.topic.ilike(pattern, escape="\\"),
            )
        )
    if subject and subject.strip():
        pattern = f"%{_escape_like(subject.strip())}%"
        stmt = stmt.where(Note.subject.ilike(pattern, escape="\\"))
    if academic_year is not None:
        stmt = stmt.where(Note.academic_year == academic_year)
    if semester is not None:
        stmt = stmt.where(Note.semester == semester)
    return stmt


@router.get("", response_model=NoteListResponse, summary="List notes")
def list_notes(
    query: str | None = Query(None, max_length=200, description="Keyword search"),
    subject: str | None = Query(None, max_length=100),
    academic_year: int | None = Query(None, ge=1, le=4),
    semester: int | None = Query(None, ge=1, le=8),
    sort: Literal["newest", "downloads"] = Query("newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    session: Session = Depends(get_session),
) -> NoteListResponse:
    filtered = _apply_filters(
        select(Note),
        query=query,
        subject=subject,
        academic_year=academic_year,
        semester=semester,
    )

    total = session.scalar(select(func.count()).select_from(filtered.subquery())) or 0

    if sort == "downloads":
        ordering = (Note.download_count.desc(), Note.id.desc())
    else:
        ordering = (Note.created_at.desc(), Note.id.desc())

    stmt = (
        filtered.order_by(*ordering)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.scalars(stmt).all()

    total_pages = math.ceil(total / page_size) if total else 0

    return NoteListResponse(
        items=[NoteRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{note_id}", response_model=NoteRead, summary="Get one note")
def get_note(note_id: int, session: Session = Depends(get_session)) -> NoteRead:
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)


@router.post(
    "",
    status_code=201,
    response_model=NoteRead,
    summary="Upload a note (PDF)",
)
def create_note(
    title: Annotated[str, Form(min_length=1, max_length=200)],
    subject: Annotated[str, Form(min_length=1, max_length=100)],
    academic_year: Annotated[int, Form(ge=1, le=4)],
    semester: Annotated[int, Form(ge=1, le=8)],
    file: Annotated[UploadFile, File(description="PDF file, max 10 MB")],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    description: Annotated[str | None, Form()] = None,
    topic: Annotated[str | None, Form(max_length=150)] = None,
) -> NoteRead:
    """Store the PDF, then persist its metadata.

    Only authenticated users may upload; listing and downloads stay public.
    The uploader's email must be verified first. The file is validated and
    written first; if the database write then fails, the new file is removed so
    storage and the database stay consistent.
    """

    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email address before uploading notes",
        )

    saved = files.save_pdf(file, settings.upload_dir, settings.max_upload_size)

    note = Note(
        title=title,
        description=description,
        subject=subject,
        academic_year=academic_year,
        semester=semester,
        topic=topic,
        file_original_name=files.sanitize_display_name(file.filename),
        stored_filename=saved.stored_filename,
        file_size=saved.file_size,
    )

    try:
        session.add(note)
        session.commit()
        session.refresh(note)
    except Exception:
        session.rollback()
        files.delete_stored_pdf(saved.path)
        raise HTTPException(
            status_code=500, detail="Could not save note metadata"
        ) from None

    return NoteRead.model_validate(note)


@router.get(
    "/{note_id}/download",
    response_class=FileResponse,
    summary="Download a note's PDF",
)
def download_note(
    note_id: int, session: Session = Depends(get_session)
) -> FileResponse:
    """Serve the stored PDF.

    The download counter is incremented and committed immediately before the
    response is returned. If the client aborts the transfer afterwards the
    count may still have advanced; that is acceptable for the MVP.
    """

    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        path = files.resolve_stored_path(settings.upload_dir, note.stored_filename)
    except files.FileValidationError:
        raise HTTPException(status_code=404, detail="Stored file not found") from None

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")

    note.download_count += 1
    session.commit()

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=files.sanitize_display_name(note.file_original_name),
    )
