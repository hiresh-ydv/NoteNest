"""Pydantic schema validation and serialization tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Note
from app.schemas import NoteBase, NoteRead


def test_note_read_serializes_a_persisted_model(session: Session) -> None:
    note = Note(
        title="DBMS Notes",
        description=None,
        subject="DBMS",
        academic_year=2,
        semester=3,
        topic=None,
        file_original_name="dbms.pdf",
        stored_filename="deadbeef.pdf",
        file_size=2048,
    )
    session.add(note)
    session.commit()
    session.refresh(note)

    data = NoteRead.model_validate(note).model_dump()

    assert data["id"] == note.id
    assert data["title"] == "DBMS Notes"
    assert data["download_count"] == 0
    assert "stored_filename" not in data


@pytest.mark.parametrize(
    "overrides",
    [
        {"academic_year": 5},
        {"academic_year": 0},
        {"semester": 9},
        {"semester": 0},
        {"title": ""},
        {"subject": ""},
        {"topic": "x" * 151},
    ],
)
def test_note_base_rejects_invalid_values(overrides: dict[str, object]) -> None:
    payload: dict[str, object] = {
        "title": "Valid title",
        "subject": "Valid subject",
        "academic_year": 1,
        "semester": 1,
    }
    payload.update(overrides)

    with pytest.raises(ValidationError):
        NoteBase(**payload)


def test_note_base_accepts_valid_values() -> None:
    schema = NoteBase(
        title="Valid title",
        subject="Valid subject",
        academic_year=4,
        semester=8,
    )

    assert schema.academic_year == 4
    assert schema.semester == 8
