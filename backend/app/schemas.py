"""Pydantic schemas.

Schemas are kept separate from SQLAlchemy models. ``NoteRead`` is the public
shape returned by the API: it deliberately omits ``stored_filename`` so the
internal file identifier is never exposed.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Registration input. The password minimum length is enforced here."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Login input. Length is not enforced so failures stay generic."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    """Safe public user fields. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class NoteBase(BaseModel):
    """Fields shared by note input validation and output."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    subject: str = Field(min_length=1, max_length=100)
    academic_year: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=8)
    topic: str | None = Field(default=None, max_length=150)


class NoteRead(NoteBase):
    """Public note metadata returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_original_name: str
    file_size: int = Field(gt=0)
    download_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    """A page of notes plus pagination metadata."""

    items: list[NoteRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
