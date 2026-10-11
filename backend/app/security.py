"""Password hashing and session-token helpers.

Kept deliberately small and free of web-framework concerns so it can be unit
tested directly and reused by the auth dependency and routes.

- Passwords: Argon2id via the maintained ``argon2-cffi`` library.
- Sessions: a signed JWT (HS256) carried in an HttpOnly cookie. We use the
  maintained ``PyJWT`` library rather than hand-rolling any cryptography.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Return an Argon2id hash for ``password`` (salt generated internally)."""

    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return whether ``password`` matches ``password_hash``.

    Any malformed or mismatched hash is treated as a failed verification; the
    caller must not distinguish the two cases.
    """

    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def generate_otp(length: int) -> str:
    """Return a random numeric one-time code of ``length`` digits."""

    return "".join(secrets.choice("0123456789") for _ in range(length))


def create_access_token(
    subject: str, secret_key: str, ttl_seconds: int
) -> tuple[str, int]:
    """Create a signed session token for ``subject`` (the user id).

    Returns the encoded token and its lifetime in seconds.
    """

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    return token, ttl_seconds


def decode_access_token(token: str, secret_key: str) -> dict:
    """Decode and validate a session token.

    Raises ``jwt.PyJWTError`` (including ``ExpiredSignatureError``) when the
    token is missing, malformed, tampered with, or expired.
    """

    return jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
