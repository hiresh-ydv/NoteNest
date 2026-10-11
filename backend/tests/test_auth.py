"""Authentication and authorization tests (Phase 6, Part B)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Note, User
from app.security import create_access_token
from app.seed import SAMPLES, seed_notes

AUTH = "/api/v1/auth"
NOTES = "/api/v1/notes"


@pytest.fixture(autouse=True)
def _isolated_db(session: Session) -> None:
    """Give every auth test a clean schema, even tests that only need client."""

    yield

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
)

CREDENTIALS = {"email": "student@example.com", "password": "password123"}


def _register(client: TestClient, **overrides: str):
    payload = {**CREDENTIALS, **overrides}
    return client.post(f"{AUTH}/register", json=payload)


# --- Registration ---------------------------------------------------------


def test_valid_registration_succeeds(client: TestClient) -> None:
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "student@example.com"
    assert body["id"] > 0
    assert "created_at" in body


def test_registration_response_never_exposes_password(client: TestClient) -> None:
    response = _register(client)

    body = response.json()
    assert "password" not in body
    assert "password_hash" not in body
    assert "password" not in response.text
    assert "hash" not in response.text


def test_duplicate_normalized_email_is_rejected(client: TestClient) -> None:
    assert _register(client, email="Student@Example.com").status_code == 201
    second = _register(client, email="student@example.com")

    assert second.status_code == 409


def test_stored_email_is_normalized(
    session: Session, client: TestClient
) -> None:
    _register(client, email="Student@Example.com")

    user = session.scalars(select(User)).one()
    assert user.email == "student@example.com"


def test_password_is_hashed_not_plaintext(
    session: Session, client: TestClient
) -> None:
    _register(client, password="supersecret123")

    user = session.scalars(select(User)).one()
    assert user.password_hash != "supersecret123"
    assert user.password_hash.startswith("$argon2id$")


def test_invalid_email_is_rejected(client: TestClient) -> None:
    assert _register(client, email="not-an-email").status_code == 422


def test_short_password_is_rejected(client: TestClient) -> None:
    assert _register(client, password="short").status_code == 422


# --- Login and session ----------------------------------------------------


def test_login_with_correct_credentials_succeeds(client: TestClient) -> None:
    _register(client)
    client.post(f"{AUTH}/logout")

    response = client.post(f"{AUTH}/login", json=CREDENTIALS)

    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_login_failure_is_generic_for_wrong_password(client: TestClient) -> None:
    _register(client)
    client.post(f"{AUTH}/logout")

    response = client.post(
        f"{AUTH}/login", json={**CREDENTIALS, "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_failure_is_generic_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        f"{AUTH}/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get(f"{AUTH}/me").status_code == 401


def test_me_returns_user_when_authenticated(client: TestClient) -> None:
    _register(client)

    response = client.get(f"{AUTH}/me")

    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_session_cookie_is_httponly(client: TestClient) -> None:
    response = _register(client)

    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_logout_clears_session(client: TestClient) -> None:
    _register(client)
    assert client.get(f"{AUTH}/me").status_code == 200

    logout = client.post(f"{AUTH}/logout")
    assert logout.status_code == 204

    assert client.get(f"{AUTH}/me").status_code == 401


def test_expired_token_is_rejected(client: TestClient) -> None:
    settings = get_settings()
    token, _ = create_access_token("1", settings.secret_key, ttl_seconds=-10)
    client.cookies.set(settings.cookie_name, token)

    assert client.get(f"{AUTH}/me").status_code == 401


def test_invalid_token_is_rejected(client: TestClient) -> None:
    settings = get_settings()
    client.cookies.set(settings.cookie_name, "not-a-real-token")

    assert client.get(f"{AUTH}/me").status_code == 401


# --- Authorization and regression ----------------------------------------


def _upload(client: TestClient):
    return client.post(
        NOTES,
        data={
            "title": "Auth Test Note",
            "subject": "Physics",
            "academic_year": "2",
            "semester": "3",
        },
        files={"file": ("note.pdf", MINIMAL_PDF, "application/pdf")},
    )


def test_unauthenticated_upload_is_rejected(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    response = _upload(client)

    assert response.status_code == 401
    assert list(upload_dir.iterdir()) == []
    assert session.scalar(select(func.count()).select_from(Note)) == 0


def test_authenticated_upload_succeeds(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    _register(client)

    response = _upload(client)

    assert response.status_code == 201
    assert session.scalar(select(func.count()).select_from(Note)) == 1


def test_public_endpoints_require_no_auth(client: TestClient) -> None:
    assert client.get(NOTES).status_code == 200
    assert client.get(f"{NOTES}/999999").status_code == 404


def test_seeded_notes_survive_account_creation(
    session: Session, client: TestClient, upload_dir: Path
) -> None:
    seed_notes(session, upload_dir, get_settings().max_upload_size)
    before = client.get(NOTES).json()["total"]
    assert before == len(SAMPLES)

    _register(client)

    after = client.get(NOTES).json()["total"]
    assert after == before
