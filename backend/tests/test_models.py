"""Note model persistence and constraint tests."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Note


def _valid_note(**overrides: object) -> Note:
    data: dict[str, object] = {
        "title": "Operating Systems Notes",
        "description": "Units 1 to 5",
        "subject": "Operating Systems",
        "academic_year": 3,
        "semester": 5,
        "topic": "CPU Scheduling",
        "file_original_name": "os-notes.pdf",
        "stored_filename": "0123456789abcdef.pdf",
        "file_size": 12345,
    }
    data.update(overrides)
    return Note(**data)


def test_create_and_retrieve_note(session: Session) -> None:
    note = _valid_note()
    session.add(note)
    session.commit()
    session.refresh(note)

    assert note.id is not None

    fetched = session.get(Note, note.id)
    assert fetched is not None
    assert fetched.title == "Operating Systems Notes"
    assert fetched.academic_year == 3
    assert fetched.semester == 5
    assert fetched.download_count == 0
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "subject",
        "file_original_name",
        "stored_filename",
        "file_size",
        "academic_year",
        "semester",
    ],
)
def test_required_fields_are_enforced(session: Session, field: str) -> None:
    note = _valid_note()
    setattr(note, field, None)
    session.add(note)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("year", [0, 5, -1])
def test_academic_year_range_enforced(session: Session, year: int) -> None:
    session.add(_valid_note(academic_year=year))

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("semester", [0, 9, -1])
def test_semester_range_enforced(session: Session, semester: int) -> None:
    session.add(_valid_note(semester=semester))

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("size", [0, -10])
def test_file_size_must_be_positive(session: Session, size: int) -> None:
    session.add(_valid_note(file_size=size))

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
