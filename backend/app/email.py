"""Outbound email for OTP verification.

Uses only the standard library (``smtplib``), so no extra dependency is
required and any SMTP provider works (Gmail, Brevo, and so on). When SMTP is
not configured, the code is written to the log instead of being sent, which
keeps local development and the test suite fully offline.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import Settings

logger = logging.getLogger("notenest.email")


def is_configured(settings: Settings) -> bool:
    """Return whether enough SMTP settings are present to send mail."""

    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_otp_email(to_email: str, code: str, settings: Settings) -> bool:
    """Send a verification code to ``to_email``.

    Returns ``True`` when the message was handed to the SMTP server and
    ``False`` when it was only logged (SMTP unconfigured) or the send failed.
    A failure never raises: registration must not break because email is down.
    """

    minutes = max(1, settings.otp_ttl_seconds // 60)

    if not is_configured(settings):
        logger.warning(
            "SMTP is not configured; verification code for %s is %s "
            "(development mode, no email sent)",
            to_email,
            code,
        )
        return False

    message = EmailMessage()
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to_email
    message["Subject"] = "Your NoteNest verification code"
    message.set_content(
        f"Your NoteNest verification code is {code}.\n\n"
        f"It expires in {minutes} minutes. "
        "If you did not request it, you can ignore this email."
    )

    try:
        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=15
        ) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Failed to send verification email to %s", to_email)
        return False
