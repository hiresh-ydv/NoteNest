"""Authentication endpoints: register, login, logout, and current user.

The session is a signed JWT carried in an HttpOnly cookie, so frontend
JavaScript can never read the credential. See ``app.security`` for hashing and
token details, and the README for the cookie/CORS/CSRF configuration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import email as email_service
from app import security
from app.config import get_settings
from app.database import get_session
from app.models import User
from app.schemas import (
    MessageResponse,
    UserLogin,
    UserRead,
    UserRegister,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


def normalize_email(email: str) -> str:
    """Return the canonical stored form of an email address."""

    return email.strip().lower()


def _as_utc(value: datetime) -> datetime:
    """Interpret naive datetimes (as SQLite returns) as UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _issue_otp(user: User, session: Session) -> None:
    """Create a fresh verification code for ``user`` and email it.

    Only the hash is stored. Sending is best-effort: when SMTP is unconfigured
    (development and tests) the code is written to the log instead.
    """

    code = security.generate_otp(settings.otp_length)
    now = datetime.now(timezone.utc)
    user.otp_hash = security.hash_password(code)
    user.otp_expires_at = now + timedelta(seconds=settings.otp_ttl_seconds)
    user.otp_attempts = 0
    user.otp_last_sent_at = now
    session.commit()
    email_service.send_otp_email(user.email, code, settings)


def _set_session_cookie(response: Response, user_id: int) -> None:
    token, ttl = security.create_access_token(
        subject=str(user_id),
        secret_key=settings.secret_key,
        ttl_seconds=settings.access_token_ttl,
    )
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=ttl,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    # Attributes must match those used when setting the cookie.
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def get_current_user(
    request: Request, session: Session = Depends(get_session)
) -> User:
    """Resolve the authenticated user from the session cookie or raise 401."""

    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = security.decode_access_token(token, settings.secret_key)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        ) from None

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        ) from None

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(
    payload: UserRegister,
    response: Response,
    session: Session = Depends(get_session),
) -> UserRead:
    email = normalize_email(payload.email)

    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(email=email, password_hash=security.hash_password(payload.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # Handles the race where another request inserted the same email.
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None

    session.refresh(user)
    _issue_otp(user, session)
    _set_session_cookie(response, user.id)
    return UserRead.model_validate(user)


@router.post("/login", response_model=UserRead, summary="Log in")
def login(
    payload: UserLogin,
    response: Response,
    session: Session = Depends(get_session),
) -> UserRead:
    email = normalize_email(payload.email)
    user = session.scalar(select(User).where(User.email == email))

    # Same message whether the email is unknown or the password is wrong.
    if user is None or not security.verify_password(
        user.password_hash, payload.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    _set_session_cookie(response, user.id)
    return UserRead.model_validate(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(response)
    return response


@router.get("/me", response_model=UserRead, summary="Current user")
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/verify-email",
    response_model=UserRead,
    summary="Verify the email address with a code",
)
def verify_email(
    payload: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserRead:
    """Confirm the signed-in user's email using the emailed one-time code."""

    if current_user.email_verified:
        return UserRead.model_validate(current_user)

    if current_user.otp_hash is None or current_user.otp_expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code is pending. Request a new one.",
        )

    if _as_utc(current_user.otp_expires_at) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This code has expired. Request a new one.",
        )

    if current_user.otp_attempts >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Request a new code.",
        )

    if not security.verify_password(current_user.otp_hash, payload.code.strip()):
        current_user.otp_attempts += 1
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect code",
        )

    current_user.email_verified = True
    current_user.otp_hash = None
    current_user.otp_expires_at = None
    current_user.otp_attempts = 0
    session.commit()
    session.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.post(
    "/resend-otp",
    response_model=MessageResponse,
    summary="Send a new verification code",
)
def resend_otp(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MessageResponse:
    """Issue a new code for the signed-in user, rate-limited by a cooldown."""

    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already verified.",
        )

    if current_user.otp_last_sent_at is not None:
        elapsed = (
            datetime.now(timezone.utc) - _as_utc(current_user.otp_last_sent_at)
        ).total_seconds()
        remaining = settings.otp_resend_cooldown_seconds - elapsed
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {int(remaining) + 1} seconds before requesting another code.",
            )

    _issue_otp(current_user, session)
    return MessageResponse(detail="A new verification code has been sent.")
