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


def test_build_templates_escape_html_output() -> None:
    username = 'Alice <img src=x onerror="x">'
    url = 'https://example.com/verify?t=a" onclick="alert(1)'

    verification_payload = build_verification_email(username, url)
    resend_payload = build_resend_verification_email(username, url)
    reset_payload = build_password_reset_email(username, url)

    assert "<img" in verification_payload.body_text
    assert "&lt;img" in verification_payload.body_html
    assert "onerror=&quot;x&quot;" in verification_payload.body_html
    assert "&quot; onclick=&quot;alert(1)" in verification_payload.body_html

    assert "&lt;img" in resend_payload.body_html
    assert "&quot; onclick=&quot;alert(1)" in resend_payload.body_html

    assert "&lt;img" in reset_payload.body_html
    assert "&quot; onclick=&quot;alert(1)" in reset_payload.body_html
