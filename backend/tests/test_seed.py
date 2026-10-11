"""Demo seed data tests.

These run against the isolated test database and upload directory, so the
development database is never touched.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Note
from app.seed import SAMPLES, seed_notes

BASE = "/api/v1/notes"


def test_sample_set_is_large_and_varied() -> None:
    assert 8 <= len(SAMPLES) <= 12

    subjects = {sample.subject for sample in SAMPLES}
    years = {sample.academic_year for sample in SAMPLES}
    semesters = {sample.semester for sample in SAMPLES}

    assert len(subjects) >= 5
    assert years <= {1, 2, 3, 4}
    assert years == {1, 2, 3, 4}
    assert semesters <= {1, 2, 3, 4, 5, 6, 7, 8}


def test_seed_creates_notes_with_readable_pdfs(
    session: Session, upload_dir: Path
) -> None:
    result = seed_notes(session, upload_dir, get_settings().max_upload_size)

    assert len(result["created"]) == len(SAMPLES)
    assert result["skipped"] == []

    notes = session.scalars(select(Note)).all()
    assert len(notes) == len(SAMPLES)

    for note in notes:
        stored = upload_dir / note.stored_filename
        assert stored.is_file()
        data = stored.read_bytes()
        assert data.startswith(b"%PDF-")
        assert data.rstrip().endswith(b"%%EOF")
        assert note.file_size == len(data)
        assert note.file_size > 0


def test_seed_is_idempotent(session: Session, upload_dir: Path) -> None:
    seed_notes(session, upload_dir, get_settings().max_upload_size)
    second = seed_notes(session, upload_dir, get_settings().max_upload_size)

    assert second["created"] == []
    assert len(second["skipped"]) == len(SAMPLES)
    assert session.scalar(select(func.count()).select_from(Note)) == len(SAMPLES)


def test_seeded_notes_are_served_through_the_api(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    seed_notes(session, upload_dir, get_settings().max_upload_size)

    listing = client.get(BASE).json()
    assert listing["total"] == len(SAMPLES)

    search = client.get(BASE, params={"query": "operating systems"}).json()
    assert search["total"] >= 1

    filtered = client.get(
        BASE, params={"academic_year": 1, "semester": 2}
    ).json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["subject"] == "Mathematics"

    note_id = listing["items"][0]["id"]
    detail = client.get(f"{BASE}/{note_id}")
    assert detail.status_code == 200

    download = client.get(f"{BASE}/{note_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.content.startswith(b"%PDF-")
