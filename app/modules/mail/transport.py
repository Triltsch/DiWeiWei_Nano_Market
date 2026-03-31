"""Asynchronous SMTP transport with retry and safe logging."""

import asyncio
import hashlib
import logging
from contextvars import ContextVar
from email.message import EmailMessage
from time import perf_counter
from typing import Final
from uuid import uuid4

from aiosmtplib import SMTP, SMTPException
from aiosmtplib.errors import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPConnectResponseError,
    SMTPRecipientRefused,
    SMTPResponseException,
    SMTPServerDisconnected,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

MAX_BACKOFF_SECONDS: Final[float] = 30.0
DEFAULT_MESSAGE_TYPE: Final[str] = "generic"

_message_type_var: ContextVar[str] = ContextVar("mail_message_type", default=DEFAULT_MESSAGE_TYPE)
_correlation_id_var: ContextVar[str] = ContextVar("mail_correlation_id", default="")


class SMTPDeliveryError(Exception):
    """Raised when message delivery fails due to transport/runtime issues."""

    def __init__(self, message: str, *, attempts: int) -> None:
        super().__init__(message)
        self.attempts = attempts


class SMTPAuthError(Exception):
    """Raised when SMTP authentication fails and no retry should occur."""


def set_mail_context(message_type: str, correlation_id: str | None = None) -> None:
    """Set contextual metadata used for structured delivery logs."""
    normalized_type = message_type.strip() if message_type.strip() else DEFAULT_MESSAGE_TYPE
    _message_type_var.set(normalized_type)
    _correlation_id_var.set(correlation_id or str(uuid4()))


def _validate_header_value(field_name: str, value: str) -> None:
    if "\r" in value or "\n" in value:
        raise ValueError(
            f"Invalid mail header value for {field_name}: CRLF characters are not allowed"
        )


def _destination_domain_hash(recipient: str) -> str:
    domain = recipient.rsplit("@", maxsplit=1)[-1].lower()
    return hashlib.sha256(domain.encode("utf-8")).hexdigest()


def _is_transient_error(error: Exception) -> bool:
    if isinstance(error, SMTPRecipientRefused):
        return 400 <= error.code < 500

    if isinstance(error, SMTPResponseException):
        code = getattr(error, "code", None)
        if isinstance(code, int):
            return 400 <= code < 500

    if isinstance(error, SMTPConnectResponseError):
        code = getattr(error, "code", None)
        if isinstance(code, int):
            return 400 <= code < 500

    return False


def _is_auth_error(error: Exception) -> bool:
    if isinstance(error, SMTPAuthenticationError):
        return True

    if isinstance(error, SMTPResponseException):
        code = getattr(error, "code", None)
        if code == 535:
            return True

    return False


async def _deliver_with_client(*, to: str, subject: str, body_html: str, body_text: str) -> None:
    settings = get_settings()
    smtp_settings = settings.smtp_settings

    _validate_header_value("to", to)
    _validate_header_value("subject", subject)
    _validate_header_value("from", smtp_settings.smtp_from_address)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{smtp_settings.smtp_from_name} <{smtp_settings.smtp_from_address}>"
    message["To"] = to
    message.set_content(body_text)
    message.add_alternative(body_html, subtype="html")

    smtp_client = SMTP(
        hostname=smtp_settings.smtp_host,
        port=smtp_settings.smtp_port,
        use_tls=smtp_settings.smtp_use_tls,
        timeout=smtp_settings.smtp_connect_timeout_seconds,
    )

    await smtp_client.connect()
    try:
        if smtp_settings.smtp_use_starttls:
            await smtp_client.starttls(timeout=smtp_settings.smtp_read_timeout_seconds)

        await smtp_client.login(
            smtp_settings.smtp_username,
            smtp_settings.smtp_password.get_secret_value(),
            timeout=smtp_settings.smtp_read_timeout_seconds,
        )
        await smtp_client.send_message(message, timeout=smtp_settings.smtp_read_timeout_seconds)
    finally:
        try:
            await smtp_client.quit()
        except SMTPException:
            logger.debug("smtp_quit_failed", exc_info=True)


async def send_mail(to: str, subject: str, body_html: str, body_text: str) -> None:
    """Send an email asynchronously using SMTP settings with bounded retry."""
    settings = get_settings()
    smtp_settings = settings.smtp_settings

    message_type = _message_type_var.get() or DEFAULT_MESSAGE_TYPE
    correlation_id = _correlation_id_var.get() or str(uuid4())
    destination_domain_hash = _destination_domain_hash(to)

    max_attempts = max(1, smtp_settings.smtp_retry_max_attempts)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        started_at = perf_counter()
        try:
            await _deliver_with_client(
                to=to, subject=subject, body_html=body_html, body_text=body_text
            )
            latency_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "smtp_delivery_attempt",
                extra={
                    "message_type": message_type,
                    "destination_domain_hash": destination_domain_hash,
                    "correlation_id": correlation_id,
                    "result": "success",
                    "attempt": attempt,
                    "latency_ms": round(latency_ms, 2),
                },
            )
            return
        except Exception as error:  # pragma: no cover - exercised by tests via subclasses
            last_error = error
            latency_ms = (perf_counter() - started_at) * 1000

            if isinstance(error, ValueError):
                raise

            logger.warning(
                "smtp_delivery_attempt",
                extra={
                    "message_type": message_type,
                    "destination_domain_hash": destination_domain_hash,
                    "correlation_id": correlation_id,
                    "result": "failed",
                    "attempt": attempt,
                    "latency_ms": round(latency_ms, 2),
                    "error_type": error.__class__.__name__,
                },
            )

            if _is_auth_error(error):
                logger.error(
                    "smtp_auth_failed",
                    extra={
                        "message_type": message_type,
                        "destination_domain_hash": destination_domain_hash,
                        "correlation_id": correlation_id,
                        "attempt": attempt,
                    },
                )
                raise SMTPAuthError("SMTP authentication failed") from error

            transient = _is_transient_error(error)

            if transient and attempt < max_attempts:
                backoff_seconds = min(
                    smtp_settings.smtp_retry_backoff_seconds * attempt, MAX_BACKOFF_SECONDS
                )
                await asyncio.sleep(backoff_seconds)
                continue

            if isinstance(
                error, (asyncio.TimeoutError, SMTPConnectError, SMTPServerDisconnected, OSError)
            ):
                raise SMTPDeliveryError(
                    "SMTP delivery failed due to timeout or connection error", attempts=attempt
                ) from error

            if transient and attempt >= max_attempts:
                logger.error(
                    "smtp_retries_exhausted",
                    extra={
                        "message_type": message_type,
                        "destination_domain_hash": destination_domain_hash,
                        "correlation_id": correlation_id,
                        "attempts": attempt,
                    },
                )
                raise SMTPDeliveryError(
                    "SMTP delivery failed after retry exhaustion", attempts=attempt
                ) from error

            raise SMTPDeliveryError("SMTP delivery failed", attempts=attempt) from error

    raise SMTPDeliveryError("SMTP delivery failed", attempts=max_attempts) from last_error
