"""Seed the notes library with clearly labelled demo content.

This is a development utility, not part of the running application. It exists
so the site can be demonstrated with realistic content. It reuses the same
validated file service as a real upload, so PDF validation, safe random stored
names, and the configured upload directory all behave exactly as in production.

Idempotency: a note is considered already seeded when a note with the same
title exists. Running the command again creates nothing new and deletes
nothing. Existing (including user-uploaded) notes are never touched.

Usage (from the ``backend`` directory)::

    python -m app.seed
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import Note
from app.services import files

SEED_MARKER = "NoteNest demo sample"


@dataclass(frozen=True)
class Sample:
    """One fictional demo note."""

    title: str
    subject: str
    academic_year: int
    semester: int
    topic: str
    summary: str
    bullets: tuple[str, ...]


SAMPLES: tuple[Sample, ...] = (
    Sample(
        title="Database Management Systems: ER Modelling and Normalization",
        subject="Database Management Systems",
        academic_year=2,
        semester=3,
        topic="ER model and normalization",
        summary=(
            "Demonstration notes covering entity-relationship diagrams and the "
            "first three normal forms."
        ),
        bullets=(
            "Entities, attributes and relationship cardinalities.",
            "Converting an ER diagram into relational tables.",
            "1NF, 2NF and 3NF with a small worked example.",
            "Why normalization reduces redundancy and update anomalies.",
        ),
    ),
    Sample(
        title="Data Structures: Arrays, Linked Lists and Stacks",
        subject="Data Structures",
        academic_year=2,
        semester=3,
        topic="Linear structures",
        summary=(
            "Demonstration notes comparing contiguous arrays with linked lists "
            "and the stack abstract data type."
        ),
        bullets=(
            "Array indexing, resizing and cache behaviour.",
            "Singly and doubly linked list traversal.",
            "Stack push and pop with an array implementation.",
            "Choosing a structure by access and update cost.",
        ),
    ),
    Sample(
        title="Operating Systems: Process Scheduling Basics",
        subject="Operating Systems",
        academic_year=3,
        semester=5,
        topic="CPU scheduling",
        summary=(
            "Demonstration notes on process states and common CPU scheduling "
            "policies."
        ),
        bullets=(
            "Ready, running and waiting process states.",
            "First come first served and shortest job first.",
            "Round robin and the effect of time quantum.",
            "Throughput, waiting time and response time metrics.",
        ),
    ),
    Sample(
        title="Engineering Mathematics: Matrices and Determinants",
        subject="Mathematics",
        academic_year=1,
        semester=2,
        topic="Linear algebra",
        summary=(
            "Demonstration notes on matrix operations, determinants and systems "
            "of linear equations."
        ),
        bullets=(
            "Matrix addition, multiplication and transpose.",
            "Computing determinants of 2x2 and 3x3 matrices.",
            "Solving linear systems with Cramer's rule.",
            "Rank of a matrix and consistency of a system.",
        ),
    ),
    Sample(
        title="Computer Networks: TCP/IP Layers Explained",
        subject="Computer Networks",
        academic_year=3,
        semester=6,
        topic="TCP/IP",
        summary=(
            "Demonstration notes walking through the four TCP/IP layers and "
            "encapsulation."
        ),
        bullets=(
            "Application, transport, internet and link layers.",
            "Encapsulation of data down the stack.",
            "How TCP establishes a connection with a handshake.",
            "Where IP addressing and routing fit in.",
        ),
    ),
    Sample(
        title="Discrete Mathematics: Set Theory and Relations",
        subject="Discrete Mathematics",
        academic_year=1,
        semester=1,
        topic="Sets and relations",
        summary=(
            "Demonstration notes on sets, functions and equivalence relations."
        ),
        bullets=(
            "Set notation, union, intersection and complement.",
            "Cartesian products and binary relations.",
            "Reflexive, symmetric and transitive properties.",
            "Equivalence classes and partitions.",
        ),
    ),
    Sample(
        title="Design and Analysis of Algorithms: Greedy Methods",
        subject="Algorithms",
        academic_year=4,
        semester=7,
        topic="Greedy algorithms",
        summary=(
            "Demonstration notes on greedy strategy, exchange arguments and "
            "classic examples."
        ),
        bullets=(
            "When a locally optimal choice is globally optimal.",
            "Activity selection and interval scheduling.",
            "Huffman coding as a greedy construction.",
            "Why greedy fails for some problems.",
        ),
    ),
    Sample(
        title="Software Engineering: SDLC and Agile Models",
        subject="Software Engineering",
        academic_year=3,
        semester=5,
        topic="Software process models",
        summary=(
            "Demonstration notes comparing waterfall and agile development "
            "lifecycles."
        ),
        bullets=(
            "Requirements, design, implementation and testing phases.",
            "Strengths and weaknesses of the waterfall model.",
            "Iterative delivery with agile sprints.",
            "The role of feedback in process selection.",
        ),
    ),
    Sample(
        title="DBMS: SQL Joins and Subqueries Cheat Sheet",
        subject="Database Management Systems",
        academic_year=2,
        semester=4,
        topic="SQL",
        summary=(
            "Demonstration notes summarising join types and common subquery "
            "patterns."
        ),
        bullets=(
            "Inner, left, right and full outer joins.",
            "Correlated versus non-correlated subqueries.",
            "Using EXISTS and IN for membership tests.",
            "Reading a query plan to spot inefficiency.",
        ),
    ),
    Sample(
        title="Operating Systems: Deadlock Detection Notes",
        subject="Operating Systems",
        academic_year=4,
        semester=8,
        topic="Deadlocks",
        summary=(
            "Demonstration notes on deadlock conditions and simple detection "
            "strategies."
        ),
        bullets=(
            "Mutual exclusion, hold and wait, no preemption, circular wait.",
            "Representing resource allocation as a graph.",
            "Detecting a cycle to find a deadlock.",
            "Prevention versus avoidance versus detection.",
        ),
    ),
)


def _escape_pdf_text(text: str) -> str:
    """Escape characters that are special inside a PDF string literal."""

    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(title: str, bullets: tuple[str, ...], footer: str) -> bytes:
    """Build a small, valid one-page PDF from plain text.

    The output is a complete PDF with a correct cross-reference table, so any
    standard PDF reader can open it.
    """

    lines = [
        f"- {bullet}" for bullet in bullets
    ] + ["", footer]

    parts = [
        "BT",
        "/F1 18 Tf",
        "72 780 Td",
        f"({_escape_pdf_text(title)}) Tj",
        "ET",
    ]
    y = 745
    for line in lines:
        parts.append("BT")
        parts.append("/F1 11 Tf")
        parts.append(f"72 {y} Td")
        parts.append(f"({_escape_pdf_text(line)}) Tj")
        parts.append("ET")
        y -= 18
    content = "\n".join(parts) + "\n"
    stream = content.encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    buffer = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(buffer))
        buffer += f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(buffer)
    size = len(objects) + 1
    buffer += f"xref\n0 {size}\n".encode("ascii")
    buffer += b"0000000000 65535 f \n"
    for offset in offsets:
        buffer += f"{offset:010d} 00000 n \n".encode("ascii")
    buffer += (
        f"trailer\n<< /Size {size} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return bytes(buffer)


def _pdf_for(sample: Sample) -> bytes:
    return build_pdf(
        sample.title,
        sample.bullets,
        f"{SEED_MARKER} for NoteNest. Fictional placeholder content.",
    )


def _display_name(sample: Sample) -> str:
    slug = "".join(
        character if character.isalnum() else "-"
        for character in sample.title.lower()
    )
    while "--" in slug:
        slug = slug.replace("--", "-")
    return files.sanitize_display_name(f"{slug.strip('-')[:120]}.pdf")


def seed_notes(
    session: Session,
    upload_dir: Path,
    max_size: int,
) -> dict[str, list[str]]:
    """Create any missing demo notes and return what was created or skipped."""

    existing_titles = set(session.scalars(select(Note.title)).all())
    created: list[str] = []
    skipped: list[str] = []

    for sample in SAMPLES:
        if sample.title in existing_titles:
            skipped.append(sample.title)
            continue

        upload = UploadFile(
            file=BytesIO(_pdf_for(sample)),
            filename=_display_name(sample),
        )
        saved = files.save_pdf(upload, Path(upload_dir), max_size)

        session.add(
            Note(
                title=sample.title,
                description=sample.summary,
                subject=sample.subject,
                academic_year=sample.academic_year,
                semester=sample.semester,
                topic=sample.topic,
                file_original_name=files.sanitize_display_name(upload.filename),
                stored_filename=saved.stored_filename,
                file_size=saved.file_size,
            )
        )
        created.append(sample.title)

    session.commit()
    return {"created": created, "skipped": skipped}


def main() -> None:
    settings = get_settings()
    init_db()

    session = SessionLocal()
    try:
        result = seed_notes(session, settings.upload_dir, settings.max_upload_size)
    finally:
        session.close()

    print(f"Seed marker: {SEED_MARKER}")
    print(f"Created {len(result['created'])} demo note(s).")
    print(f"Skipped {len(result['skipped'])} already-present note(s).")
    print(f"Upload directory: {settings.upload_dir}")


if __name__ == "__main__":
    main()
