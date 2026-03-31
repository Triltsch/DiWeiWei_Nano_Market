"""SMTP settings configuration tests.

Scope:
- validate all TLS/STARTTLS flag combinations
- enforce production restrictions for unencrypted SMTP mode
- ensure SMTP password is redacted in settings serialization and repr output
"""

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_smtp_tls_true_starttls_false_is_valid() -> None:
    """SMTP implicit TLS mode is accepted when STARTTLS is disabled."""
    settings = Settings(
        SMTP_USE_TLS=True,
        SMTP_USE_STARTTLS=False,
        SMTP_FROM_ADDRESS="no-reply@example.com",
    )

    smtp = settings.smtp_settings

    assert smtp.smtp_use_tls is True
    assert smtp.smtp_use_starttls is False


def test_smtp_tls_false_starttls_true_is_valid() -> None:
    """SMTP STARTTLS mode is accepted when implicit TLS is disabled."""
    settings = Settings(
        SMTP_USE_TLS=False,
        SMTP_USE_STARTTLS=True,
        SMTP_FROM_ADDRESS="no-reply@example.com",
    )

    smtp = settings.smtp_settings

    assert smtp.smtp_use_tls is False
    assert smtp.smtp_use_starttls is True


def test_smtp_tls_true_starttls_true_raises_validation_error() -> None:
    """Mutually enabled TLS flags are rejected with a clear validation message."""
    with pytest.raises(ValidationError, match="SMTP_USE_TLS and SMTP_USE_STARTTLS"):
        Settings(
            SMTP_USE_TLS=True,
            SMTP_USE_STARTTLS=True,
        )


def test_smtp_plaintext_allowed_in_test_environment() -> None:
    """Unencrypted SMTP mode is allowed for test and development profiles."""
    settings = Settings(
        ENV="test",
        SMTP_USE_TLS=False,
        SMTP_USE_STARTTLS=False,
        SMTP_FROM_ADDRESS="no-reply@example.com",
    )

    smtp = settings.smtp_settings

    assert smtp.smtp_use_tls is False
    assert smtp.smtp_use_starttls is False


def test_smtp_plaintext_rejected_in_production() -> None:
    """Unencrypted SMTP mode is rejected in production to prevent insecure transport."""
    with pytest.raises(ValidationError, match="not allowed in production"):
        Settings(
            ENV="production",
            SMTP_USE_TLS=False,
            SMTP_USE_STARTTLS=False,
        )


def test_get_settings_fails_fast_for_invalid_tls_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startup settings load fails immediately when both SMTP TLS flags are true."""
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "true")
    monkeypatch.setenv("SECRET_KEY", "dev-unsafe-change-me")
    monkeypatch.setenv("ENV", "development")
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="SMTP_USE_TLS and SMTP_USE_STARTTLS"):
        get_settings()

    get_settings.cache_clear()


def test_smtp_password_redacted_in_repr_and_model_dump() -> None:
    """SMTP password remains redacted in repr output and model_dump string output."""
    raw_password = "super-secret-password"
    settings = Settings(SMTP_PASSWORD=raw_password)

    assert raw_password not in repr(settings)
    assert raw_password not in str(settings.model_dump())


def test_smtp_production_rejects_development_defaults() -> None:
    """Production settings reject placeholder SMTP defaults to avoid hidden misconfiguration."""
    with pytest.raises(ValidationError, match="production requires explicit SMTP_HOST"):
        Settings(
            ENV="production",
            SMTP_USE_TLS=False,
            SMTP_USE_STARTTLS=True,
        )


def test_smtp_production_accepts_explicit_values() -> None:
    """Production settings accept explicit SMTP credentials and sender values."""
    settings = Settings(
        ENV="production",
        SMTP_HOST="smtp.example.com",
        SMTP_PORT=587,
        SMTP_USERNAME="mailer",
        SMTP_PASSWORD="strong-secret",
        SMTP_FROM_ADDRESS="notifications@example.com",
        SMTP_USE_TLS=False,
        SMTP_USE_STARTTLS=True,
    )

    smtp = settings.smtp_settings

    assert smtp.smtp_host == "smtp.example.com"
    assert smtp.smtp_username == "mailer"
