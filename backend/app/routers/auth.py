"""Authentication endpoints: register, login, logout, and current user.

The session is a signed JWT carried in an HttpOnly cookie, so frontend
JavaScript can never read the credential. See ``app.security`` for hashing and
token details, and the README for the cookie/CORS/CSRF configuration.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import security
from app.config import get_settings
from app.database import get_session
from app.models import User
from app.schemas import UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


def normalize_email(email: str) -> str:
    """Return the canonical stored form of an email address."""

    return email.strip().lower()


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
