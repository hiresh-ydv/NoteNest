"""Shared helpers for tests that need authenticated, verified users.

The fake email sender defined here is installed by an autouse fixture in
``conftest.py``; it captures one-time codes instead of sending real mail, and
posts them in ``OUTBOX`` keyed by recipient email.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

AUTH = "/api/v1/auth"

# {email: last_code}. Cleared before and after every test by conftest.
OUTBOX: dict[str, str] = {}


def fake_send_otp_email(to_email: str, code: str, settings: Any) -> bool:
    """Drop-in replacement for ``app.email.send_otp_email`` used by tests."""

    OUTBOX[to_email] = code
    return True


def code_for(email: str) -> str:
    """Return the most recently issued code for ``email``."""

    return OUTBOX[email]


def register(
    client: TestClient,
    *,
    email: str = "uploader@example.com",
    password: str = "password123",
    verify: bool = True,
) -> TestClient:
    """Register ``email`` on ``client`` and verify it unless skipped.

    Returns the same client so callers can chain assertions.
    """

    response = client.post(
        f"{AUTH}/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201, response.text
    if verify:
        verified = client.post(
            f"{AUTH}/verify-email", json={"code": code_for(email)}
        )
        assert verified.status_code == 200, verified.text
    return client