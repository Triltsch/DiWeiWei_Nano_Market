"""Unit tests for asynchronous SMTP transport behavior."""

import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from app.config import get_settings
from app.modules.mail import transport
from app.modules.mail.transport import SMTPAuthError, SMTPDeliveryError, send_mail, set_mail_context


class FakeSMTP:
    """Configurable fake SMTP client for transport unit tests."""

    last_init: dict[str, Any] = {}
    starttls_calls: int = 0
    login_calls: int = 0
    send_calls: int = 0
    connect_calls: int = 0
    quit_calls: int = 0
    auth_supported: bool = True
    send_effects: list[Callable[[], None]] = []

    def __init__(self, **kwargs: Any) -> None:
        self.__class__.last_init = kwargs

    @classmethod
    def reset(cls) -> None:
        cls.last_init = {}
        cls.starttls_calls = 0
        cls.login_calls = 0
        cls.send_calls = 0
        cls.connect_calls = 0
        cls.quit_calls = 0
        cls.auth_supported = True
        cls.send_effects = []

    async def connect(self) -> None:
        self.__class__.connect_calls += 1

    async def starttls(self, timeout: float | None = None) -> None:
        self.__class__.starttls_calls += 1

    async def login(self, username: str, password: str, timeout: float | None = None) -> None:
        _ = username
        _ = password
        _ = timeout
        self.__class__.login_calls += 1

    async def send_message(self, message: object, timeout: float | None = None) -> None:
        _ = message
        _ = timeout
        self.__class__.send_calls += 1
        if self.__class__.send_effects:
            effect = self.__class__.send_effects.pop(0)
            effect()

    async def quit(self) -> None:
        self.__class__.quit_calls += 1

    def supports_extension(self, extension_name: str) -> bool:
        return extension_name.lower() == "auth" and self.__class__.auth_supported


class TransientSMTPError(Exception):
    """Synthetic transient SMTP error used in retry tests."""


class AuthFailureError(Exception):
    """Synthetic auth failure used in immediate-failure tests."""


@pytest.fixture(autouse=True)
def _reset_mail_context(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSMTP.reset()
    get_settings.cache_clear()
    monkeypatch.setattr(transport, "SMTP", FakeSMTP)
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SMTP_HOST", "mailpit")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USERNAME", "mailpit")
    monkeypatch.setenv("SMTP_PASSWORD", "mailpit")
    monkeypatch.setenv("SMTP_FROM_ADDRESS", "no-reply@example.com")
    monkeypatch.setenv("SMTP_FROM_NAME", "DiWeiWei")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "false")
    monkeypatch.setenv("SMTP_RETRY_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("SMTP_RETRY_BACKOFF_SECONDS", "0.01")
    set_mail_context("generic", "test-correlation")


@pytest.mark.asyncio
async def test_send_mail_uses_tls_mode_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "false")
    get_settings.cache_clear()

    await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.last_init["use_tls"] is True
    assert FakeSMTP.starttls_calls == 0


@pytest.mark.asyncio
async def test_send_mail_uses_starttls_mode_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "true")
    get_settings.cache_clear()

    await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.last_init["use_tls"] is False
    assert FakeSMTP.starttls_calls == 1


@pytest.mark.asyncio
async def test_send_mail_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_once() -> None:
        raise TransientSMTPError("temporary failure")

    FakeSMTP.send_effects = [fail_once, fail_once]

    async def _no_sleep(delay: float) -> None:
        _ = delay

    monkeypatch.setattr(
        transport, "_is_transient_error", lambda error: isinstance(error, TransientSMTPError)
    )
    monkeypatch.setattr(transport, "_is_auth_error", lambda error: False)
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.send_calls == 3


@pytest.mark.asyncio
async def test_send_mail_raises_when_retries_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_always() -> None:
        raise TransientSMTPError("temporary failure")

    FakeSMTP.send_effects = [fail_always, fail_always, fail_always]

    async def _no_sleep(delay: float) -> None:
        _ = delay

    monkeypatch.setattr(
        transport, "_is_transient_error", lambda error: isinstance(error, TransientSMTPError)
    )
    monkeypatch.setattr(transport, "_is_auth_error", lambda error: False)
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    with pytest.raises(SMTPDeliveryError) as error:
        await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert error.value.attempts == 3
    assert FakeSMTP.send_calls == 3


@pytest.mark.asyncio
async def test_send_mail_auth_failure_has_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_auth() -> None:
        raise AuthFailureError("bad credentials")

    FakeSMTP.send_effects = [fail_auth]

    monkeypatch.setattr(
        transport, "_is_auth_error", lambda error: isinstance(error, AuthFailureError)
    )
    monkeypatch.setattr(transport, "_is_transient_error", lambda error: False)

    with pytest.raises(SMTPAuthError):
        await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.send_calls == 1


@pytest.mark.asyncio
async def test_send_mail_timeout_maps_to_delivery_error() -> None:
    def fail_timeout() -> None:
        raise asyncio.TimeoutError()

    FakeSMTP.send_effects = [fail_timeout]

    with pytest.raises(SMTPDeliveryError, match="timeout or connection"):
        await send_mail("user@example.com", "Hello", "<p>html</p>", "text")


@pytest.mark.asyncio
async def test_send_mail_logs_domain_hash_without_recipient(caplog) -> None:
    recipient = "person@example.com"
    set_mail_context("verification", "corr-123")

    with caplog.at_level("INFO", logger="app.modules.mail.transport"):
        await send_mail(recipient, "Hello", "<p>html</p>", "text")

    success_logs = [record for record in caplog.records if record.result == "success"]
    assert len(success_logs) == 1

    expected_hash = hashlib.sha256("example.com".encode("utf-8")).hexdigest()
    log_record = success_logs[0]
    assert log_record.destination_domain_hash == expected_hash
    assert log_record.message_type == "verification"
    assert log_record.correlation_id == "corr-123"
    assert recipient not in str(log_record.__dict__)


@pytest.mark.asyncio
async def test_send_mail_rejects_header_injection() -> None:
    with pytest.raises(ValueError, match="CRLF"):
        await send_mail("person@example.com", "Hello\nBcc:evil@example.com", "<p>html</p>", "text")

    assert FakeSMTP.connect_calls == 0


@pytest.mark.asyncio
async def test_send_mail_rejects_from_name_header_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMTP_FROM_NAME", "DiWeiWei\nBcc:evil@example.com")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CRLF"):
        await send_mail("person@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.connect_calls == 0


@pytest.mark.asyncio
async def test_send_mail_skips_login_when_server_has_no_auth_support() -> None:
    FakeSMTP.auth_supported = False

    await send_mail("user@example.com", "Hello", "<p>html</p>", "text")

    assert FakeSMTP.login_calls == 0
    assert FakeSMTP.send_calls == 1
