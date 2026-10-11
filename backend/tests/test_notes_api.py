"""Notes listing, detail, search, filter, sort, and pagination tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Note

BASE = "/api/v1/notes"
_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_note(session: Session, **overrides: object) -> Note:
    index = session.scalar(select(func.count()).select_from(Note)) or 0
    data: dict[str, object] = {
        "title": f"Note {index}",
        "description": "A short description",
        "subject": "Mathematics",
        "academic_year": 1,
        "semester": 1,
        "topic": "Algebra",
        "file_original_name": f"note-{index}.pdf",
        "stored_filename": f"stored-{index}.pdf",
        "file_size": 1000 + index,
        "download_count": 0,
        "created_at": _EPOCH + timedelta(days=index),
        "updated_at": _EPOCH + timedelta(days=index),
    }
    data.update(overrides)
    note = Note(**data)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def test_empty_library(session: Session, client: TestClient) -> None:
    body = client.get(BASE).json()

    assert body == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 12,
        "total_pages": 0,
    }


def test_list_returns_records(session: Session, client: TestClient) -> None:
    _make_note(session)
    _make_note(session)

    body = client.get(BASE).json()

    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 12
    assert body["total_pages"] == 1


def test_detail_returns_public_metadata(
    session: Session, client: TestClient
) -> None:
    note = _make_note(session, title="Linear Algebra")

    response = client.get(f"{BASE}/{note.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == note.id
    assert body["title"] == "Linear Algebra"
    assert "stored_filename" not in body


def test_detail_missing_returns_404(client: TestClient) -> None:
    assert client.get(f"{BASE}/9999").status_code == 404


def test_keyword_matches_all_supported_fields(
    session: Session, client: TestClient
) -> None:
    _make_note(session, title="Quantum Physics", description=None, topic=None)
    _make_note(session, title="Notes", description="Quantum computing")
    _make_note(session, title="Notes", subject="Quantum Studies")
    _make_note(session, title="Notes", topic="quantum dots")
    _make_note(session, title="Chemistry", description=None, topic=None)

    body = client.get(BASE, params={"query": "quantum"}).json()

    assert body["total"] == 4


def test_keyword_search_is_case_insensitive(
    session: Session, client: TestClient
) -> None:
    _make_note(session, title="Quantum Physics")

    body = client.get(BASE, params={"query": "QUANTUM"}).json()

    assert body["total"] == 1


def test_keyword_wildcards_are_treated_literally(
    session: Session, client: TestClient
) -> None:
    _make_note(session, title="50% off deals", description=None, topic=None)
    _make_note(session, title="Plain notes", description=None, topic=None)

    body = client.get(BASE, params={"query": "%"}).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "50% off deals"


def test_subject_filter_is_case_insensitive(
    session: Session, client: TestClient
) -> None:
    _make_note(session, subject="Mathematics")
    _make_note(session, subject="Physics")

    body = client.get(BASE, params={"subject": "mathematics"}).json()

    assert body["total"] == 1
    assert body["items"][0]["subject"] == "Mathematics"


def test_subject_filter_matches_partial_and_is_case_insensitive(
    session: Session, client: TestClient
) -> None:
    _make_note(session, subject="Operating Systems")
    _make_note(session, subject="Computer Networks")

    body = client.get(BASE, params={"subject": "OPERAT"}).json()

    assert body["total"] == 1
    assert body["items"][0]["subject"] == "Operating Systems"


def test_year_and_semester_filters(session: Session, client: TestClient) -> None:
    _make_note(session, academic_year=1, semester=1)
    _make_note(session, academic_year=2, semester=3)
    _make_note(session, academic_year=3, semester=5)

    year_body = client.get(BASE, params={"academic_year": 2}).json()
    assert year_body["total"] == 1
    assert year_body["items"][0]["academic_year"] == 2

    semester_body = client.get(BASE, params={"semester": 5}).json()
    assert semester_body["total"] == 1
    assert semester_body["items"][0]["semester"] == 5


def test_combined_filters_use_and_semantics(
    session: Session, client: TestClient
) -> None:
    _make_note(session, title="Quantum", subject="Physics", academic_year=2, semester=3)
    _make_note(session, title="Quantum", subject="Physics", academic_year=3, semester=5)
    _make_note(session, title="Quantum", subject="Biology", academic_year=2, semester=3)

    body = client.get(
        BASE,
        params={
            "query": "quantum",
            "subject": "physics",
            "academic_year": 2,
            "semester": 3,
        },
    ).json()

    assert body["total"] == 1
    assert body["items"][0]["subject"] == "Physics"
    assert body["items"][0]["academic_year"] == 2


def test_newest_sorting(session: Session, client: TestClient) -> None:
    _make_note(session, title="Oldest", created_at=_EPOCH)
    _make_note(session, title="Middle", created_at=_EPOCH + timedelta(days=1))
    _make_note(session, title="Newest", created_at=_EPOCH + timedelta(days=2))

    body = client.get(BASE, params={"sort": "newest"}).json()

    assert [item["title"] for item in body["items"]] == [
        "Newest",
        "Middle",
        "Oldest",
    ]


def test_downloads_sorting(session: Session, client: TestClient) -> None:
    _make_note(session, title="Low", download_count=1)
    _make_note(session, title="High", download_count=10)
    _make_note(session, title="Mid", download_count=5)

    body = client.get(BASE, params={"sort": "downloads"}).json()

    assert [item["title"] for item in body["items"]] == ["High", "Mid", "Low"]


def test_pagination_and_out_of_range_page(
    session: Session, client: TestClient
) -> None:
    for number in range(5):
        _make_note(session, title=f"Note {number}")

    first = client.get(BASE, params={"page": 1, "page_size": 2}).json()
    assert first["total"] == 5
    assert first["total_pages"] == 3
    assert len(first["items"]) == 2

    last = client.get(BASE, params={"page": 3, "page_size": 2}).json()
    assert len(last["items"]) == 1

    beyond = client.get(BASE, params={"page": 99, "page_size": 2}).json()
    assert beyond["items"] == []
    assert beyond["total"] == 5
    assert beyond["total_pages"] == 3


@pytest.mark.parametrize(
    "params",
    [
        {"academic_year": 5},
        {"academic_year": 0},
        {"semester": 9},
        {"semester": 0},
        {"sort": "oldest"},
        {"page": 0},
        {"page_size": 0},
        {"page_size": 51},
    ],
)
def test_invalid_query_parameters_return_422(
    client: TestClient, params: dict[str, object]
) -> None:
    assert client.get(BASE, params=params).status_code == 422


def test_maximum_page_size_is_allowed(client: TestClient) -> None:
    assert client.get(BASE, params={"page_size": 50}).status_code == 200
