"""Auth-mail integration tests against a real Mailpit SMTP/API container.

Scope:
- registration sends exactly one verification email via SMTP
- resend verification sends a fresh email for unverified users
- resend verification for already verified users does not send email
- SMTP unreachable path maps to stable 503 response
"""

import json
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User
from app.modules.auth.service import verify_user_email
from app.modules.mail.transport import send_mail

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.mailpit_integration]

MAILPIT_API_BASE_URL = os.getenv("MAILPIT_API_BASE_URL", "http://localhost:8025/api/v1")


def _build_registration_payload() -> dict[str, Any]:
    suffix = uuid4().hex[:10]
    return {
        "email": f"mailpit_{suffix}@example.com",
        "username": f"mailpit_{suffix}",
        "password": "SecurePassword123!",
        "first_name": "Mailpit",
        "last_name": "Integration",
        "bio": "Mail integration test",
        "preferred_language": "de",
        "accept_terms": True,
        "accept_privacy": True,
    }


async def _mailpit_get_messages() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{MAILPIT_API_BASE_URL}/messages")
    response.raise_for_status()
    payload = response.json()
    messages = payload.get("messages", [])
    if not isinstance(messages, list):
        raise AssertionError("Mailpit API returned an unexpected messages payload")
    return [message for message in messages if isinstance(message, dict)]


async def _mailpit_clear_inbox() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.delete(f"{MAILPIT_API_BASE_URL}/messages")
    if response.status_code not in (200, 204):
        raise AssertionError(f"Mailpit inbox clear failed with status {response.status_code}")


async def _mailpit_get_message_detail(message: dict[str, Any]) -> dict[str, Any]:
    message_id = message.get("ID") or message.get("id")
    if not isinstance(message_id, str) or not message_id:
        raise AssertionError("Mailpit message payload does not include a message ID")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{MAILPIT_API_BASE_URL}/message/{message_id}")
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise AssertionError("Mailpit message detail payload is not an object")
    return payload


@pytest.fixture(autouse=True)
async def _mailpit_inbox_isolation() -> AsyncIterator[None]:
    await _mailpit_clear_inbox()
    yield
    await _mailpit_clear_inbox()


@pytest.fixture(autouse=True)
def _use_real_smtp_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.auth.router.send_mail", send_mail)


@pytest.fixture(autouse=True)
def _mailpit_smtp_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "false")
    monkeypatch.setenv("SMTP_USERNAME", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_register_sends_single_verification_email_and_duplicate_sends_none(
    async_client,
) -> None:
    payload = _build_registration_payload()

    response = await async_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    messages_after_first_registration = await _mailpit_get_messages()
    assert len(messages_after_first_registration) == 1

    message = messages_after_first_registration[0]
    message_snapshot = json.dumps(message)
    assert payload["email"] in message_snapshot
    assert "Verify your email address" in message_snapshot

    message_detail = await _mailpit_get_message_detail(message)
    detail_snapshot = json.dumps(message_detail)
    assert "/verify-email?token=" in detail_snapshot

    duplicate_response = await async_client.post("/api/v1/auth/register", json=payload)

    assert duplicate_response.status_code == 409
    messages_after_duplicate = await _mailpit_get_messages()
    assert len(messages_after_duplicate) == 1


@pytest.mark.asyncio
async def test_resend_verification_sends_fresh_mail_for_unverified_user(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _build_registration_payload()
    register_response = await async_client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    await _mailpit_clear_inbox()
    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)

    resend_response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": payload["email"]}
    )

    assert resend_response.status_code == 200
    messages = await _mailpit_get_messages()
    assert len(messages) == 1

    message = messages[0]
    message_snapshot = json.dumps(message)
    assert payload["email"] in message_snapshot
    assert "Your new verification link" in message_snapshot

    message_detail = await _mailpit_get_message_detail(message)
    detail_snapshot = json.dumps(message_detail)
    assert "/verify-email?token=" in detail_snapshot


@pytest.mark.asyncio
async def test_resend_verification_for_verified_user_sends_no_email(
    async_client,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _build_registration_payload()
    register_response = await async_client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    user_id = UUID(register_response.json()["id"])
    await verify_user_email(db_session, user_id)
    await _mailpit_clear_inbox()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    resend_response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": payload["email"]}
    )

    assert resend_response.status_code == 401
    assert "already verified" in resend_response.json()["detail"].lower()
    assert await _mailpit_get_messages() == []


@pytest.mark.asyncio
async def test_register_smtp_unreachable_returns_safe_503(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _build_registration_payload()
    settings = get_settings()

    monkeypatch.setenv("SMTP_HOST", "127.0.0.1")
    monkeypatch.setenv("SMTP_PORT", "1")
    get_settings.cache_clear()

    try:
        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 503
        assert (
            response.json()["detail"]
            == "Email delivery is currently unavailable. Please try again later."
        )
        assert "smtp" not in response.text.lower()
        assert "connection" not in response.text.lower()
        assert await _mailpit_get_messages() == []
    finally:
        monkeypatch.setenv("SMTP_HOST", settings.smtp_settings.smtp_host)
        monkeypatch.setenv("SMTP_PORT", str(settings.smtp_settings.smtp_port))
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_resend_verification_rate_limit_behavior_if_enabled(
    async_client,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Document current behavior: endpoint has no dedicated resend rate limiter yet."""
    payload = _build_registration_payload()
    register_response = await async_client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    user_query = select(User).where(User.id == UUID(register_response.json()["id"]))
    result = await db_session.execute(user_query)
    user = result.scalar_one()
    user.email_verified = False
    user.verified_at = None
    db_session.add(user)
    await db_session.commit()

    await _mailpit_clear_inbox()
    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)

    first = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": payload["email"]}
    )
    second = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": payload["email"]}
    )

    assert first.status_code == 200
    assert second.status_code == 200
    messages = await _mailpit_get_messages()
    assert len(messages) == 2
