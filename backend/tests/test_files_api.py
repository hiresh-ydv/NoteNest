"""PDF upload safe-storage and download tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DEFAULT_MAX_UPLOAD_SIZE
from app.database import SessionLocal, get_session
from app.main import app
from app.models import Note

BASE = "/api/v1/notes"

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R >>\n"
    b"%%EOF\n"
)
STORED_NAME_PATTERN = re.compile(r"^[0-9a-f]{32}\.pdf$")


@pytest.fixture(autouse=True)
def _isolated_db(session: Session) -> None:
    """Give every file test a clean schema, even tests that only need client."""

    yield


def _form(**overrides: object) -> dict[str, str]:
    data: dict[str, str] = {
        "title": "Uploaded Notes",
        "description": "A description",
        "subject": "Physics",
        "academic_year": "2",
        "semester": "3",
        "topic": "Optics",
    }
    data.update({key: str(value) for key, value in overrides.items()})
    return data


def _upload(
    client: TestClient,
    *,
    content: bytes = MINIMAL_PDF,
    filename: str = "notes.pdf",
    data: dict[str, str] | None = None,
    send_file: bool = True,
):
    files = (
        {"file": (filename, content, "application/pdf")} if send_file else None
    )
    return client.post(BASE, data=data or _form(), files=files)


def _register(client: TestClient) -> TestClient:
    """Register a demo user on this client (the session cookie is stored)."""

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "uploader@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    return client


def test_default_max_upload_size_is_ten_megabytes() -> None:
    assert DEFAULT_MAX_UPLOAD_SIZE == 10 * 1024 * 1024


def test_upload_valid_pdf_creates_record_and_file(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    response = _upload(client)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Uploaded Notes"
    assert body["file_original_name"] == "notes.pdf"
    assert body["file_size"] == len(MINIMAL_PDF)
    assert body["download_count"] == 0
    assert "stored_filename" not in body

    stored_files = list(upload_dir.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == MINIMAL_PDF

    note = session.scalars(select(Note)).one()
    assert STORED_NAME_PATTERN.match(note.stored_filename)
    assert note.file_original_name == "notes.pdf"
    assert note.file_size == len(MINIMAL_PDF)


def test_upload_empty_file_is_rejected(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    response = _upload(client, content=b"")

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []
    assert session.scalar(select(func.count()).select_from(Note)) == 0


def test_upload_non_pdf_is_rejected(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    response = _upload(client, content=b"this is definitely not a pdf")

    assert response.status_code == 415
    assert list(upload_dir.iterdir()) == []
    assert session.scalar(select(func.count()).select_from(Note)) == 0


def test_upload_oversized_file_is_rejected(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    oversized = MINIMAL_PDF + b"0" * 4096

    response = _upload(client, content=oversized)

    assert response.status_code == 413
    assert list(upload_dir.iterdir()) == []
    assert session.scalar(select(func.count()).select_from(Note)) == 0


@pytest.mark.parametrize(
    "data",
    [
        {k: v for k, v in _form().items() if k != "title"},
        {**_form(), "academic_year": "5"},
        {**_form(), "semester": "9"},
    ],
)
def test_upload_metadata_validation(
    client: TestClient, data: dict[str, str]
) -> None:
    _register(client)
    response = _upload(client, data=data)

    assert response.status_code == 422


def test_upload_without_file_is_rejected(client: TestClient) -> None:
    _register(client)
    response = _upload(client, send_file=False)

    assert response.status_code == 422


def test_file_removed_when_database_write_fails(
    client: TestClient, upload_dir: Path
) -> None:
    _register(client)

    def failing_session():
        session = SessionLocal()

        def boom() -> None:
            raise RuntimeError("simulated database failure")

        session.commit = boom  # type: ignore[method-assign]
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = failing_session
    try:
        response = _upload(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert list(upload_dir.iterdir()) == []


def test_download_serves_pdf_and_increments_counter(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    note_id = _upload(client).json()["id"]

    response = client.get(f"{BASE}/{note_id}/download")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "notes.pdf" in response.headers["content-disposition"]
    assert response.content == MINIMAL_PDF

    detail = client.get(f"{BASE}/{note_id}").json()
    assert detail["download_count"] == 1


def test_download_missing_note_returns_404(client: TestClient) -> None:
    assert client.get(f"{BASE}/424242/download").status_code == 404


def test_download_missing_file_returns_404_and_keeps_counter(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    note = Note(
        title="Ghost",
        subject="Physics",
        academic_year=1,
        semester=1,
        file_original_name="ghost.pdf",
        stored_filename="deadbeefdeadbeefdeadbeefdeadbeef.pdf",
        file_size=100,
    )
    session.add(note)
    session.commit()
    session.refresh(note)

    response = client.get(f"{BASE}/{note.id}/download")

    assert response.status_code == 404
    session.refresh(note)
    assert note.download_count == 0


@pytest.mark.parametrize(
    "stored_name",
    [
        "../../outside.pdf",
        "../outside.pdf",
        "nested/outside.pdf",
        "..\\outside.pdf",
    ],
)
def test_download_path_traversal_is_rejected(
    session: Session,
    client: TestClient,
    upload_dir: Path,
    stored_name: str,
) -> None:
    note = Note(
        title="Traversal",
        subject="Physics",
        academic_year=1,
        semester=1,
        file_original_name="evil.pdf",
        stored_filename=stored_name,
        file_size=100,
    )
    session.add(note)
    session.commit()
    session.refresh(note)

    response = client.get(f"{BASE}/{note.id}/download")

    assert response.status_code == 404


def test_download_counter_increments_per_request(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)
    note_id = _upload(client).json()["id"]

    client.get(f"{BASE}/{note_id}/download")
    client.get(f"{BASE}/{note_id}/download")

    detail = client.get(f"{BASE}/{note_id}").json()
    assert detail["download_count"] == 2
