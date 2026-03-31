"""Unit tests for mail template payload builders."""

from app.modules.mail.templates import (
    build_password_reset_email,
    build_resend_verification_email,
    build_verification_email,
)


def test_build_verification_email_payload() -> None:
    payload = build_verification_email("Alice", "https://example.com/verify?t=abc")

    assert payload.message_type == "verification"
    assert payload.subject == "Verify your email address"
    assert "Alice" in payload.body_text
    assert "https://example.com/verify?t=abc" in payload.body_html


def test_build_resend_verification_email_payload() -> None:
    payload = build_resend_verification_email("Bob", "https://example.com/verify?t=xyz")

    assert payload.message_type == "resend_verification"
    assert payload.subject == "Your new verification link"
    assert "Bob" in payload.body_html
    assert "https://example.com/verify?t=xyz" in payload.body_text


def test_build_password_reset_email_payload() -> None:
    payload = build_password_reset_email("Charlie", "https://example.com/reset?t=123")

    assert payload.message_type == "password_reset"
    assert payload.subject == "Reset your password"
    assert "Charlie" in payload.body_text
    assert "https://example.com/reset?t=123" in payload.body_html
