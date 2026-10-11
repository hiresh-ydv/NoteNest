"""Focused PDF file service.

All filesystem work for notes lives here: validating uploads, writing them
under server-generated names, resolving stored paths safely, and cleaning up
on failure. Route handlers only orchestrate; they never touch raw paths.

Security notes:
- The browser MIME type and the user filename are never trusted.
- Stored names are random (uuid4 hex + ``.pdf``), so no user input reaches the
  filesystem path.
- Reads and writes are streamed in chunks so size limits are enforced without
  loading a whole file into memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

PDF_SIGNATURE = b"%PDF-"
STORED_SUFFIX = ".pdf"
CHUNK_SIZE = 1024 * 1024


class FileValidationError(Exception):
    """Raised when an uploaded or stored file is unacceptable.

    Carries the HTTP status the API should return so the service stays free of
    web-framework concerns.
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class SavedPdf:
    """Result of storing an uploaded PDF."""

    stored_filename: str
    file_size: int
    path: Path


def sanitize_display_name(filename: str | None) -> str:
    """Return a safe display/download filename (never used as a path)."""

    name = Path(filename or "").name.strip()
    if not name:
        name = "document.pdf"
    if not name.lower().endswith(STORED_SUFFIX):
        name += STORED_SUFFIX
    return name[:255]


def save_pdf(upload: UploadFile, upload_dir: Path, max_size: int) -> SavedPdf:
    """Validate and store an uploaded PDF, returning its server metadata.

    Writes to a temporary ``.part`` file first and only renames it into place
    after all checks pass, so a rejected upload never leaves a readable file.
    """

    upload_dir = Path(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{STORED_SUFFIX}"
    final_path = upload_dir / stored_filename
    temp_path = upload_dir / f"{stored_filename}.part"

    size = 0
    signature = b""

    try:
        with temp_path.open("wb") as destination:
            while True:
                chunk = upload.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                if not signature:
                    signature = chunk[: len(PDF_SIGNATURE)]
                size += len(chunk)
                if size > max_size:
                    raise FileValidationError(
                        "File exceeds the maximum allowed size",
                        status_code=413,
                    )
                destination.write(chunk)

        if size == 0:
            raise FileValidationError("File is empty", status_code=400)
        if signature != PDF_SIGNATURE:
            raise FileValidationError(
                "Only PDF files are supported",
                status_code=415,
            )

        temp_path.replace(final_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise

    return SavedPdf(
        stored_filename=stored_filename,
        file_size=size,
        path=final_path,
    )


def resolve_stored_path(upload_dir: Path, stored_filename: str) -> Path:
    """Resolve a stored filename to an absolute path inside ``upload_dir``.

    Rejects any value that is not a bare filename or that would escape the
    upload directory (path traversal).
    """

    base = Path(upload_dir).resolve()

    if not stored_filename or Path(stored_filename).name != stored_filename:
        raise FileValidationError(
            "Invalid stored file reference", status_code=404
        )

    candidate = (base / stored_filename).resolve()
    if candidate.parent != base:
        raise FileValidationError(
            "Invalid stored file reference", status_code=404
        )

    return candidate


def delete_stored_pdf(path: Path) -> None:
    """Best-effort removal of a stored file (used for rollback)."""

    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
