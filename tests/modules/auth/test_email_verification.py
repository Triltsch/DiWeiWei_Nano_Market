"""Tests for email verification functionality.

This module contains comprehensive tests for the email verification system, including:
- Token creation and validation
- Email verification workflows
- Token expiration and error handling
- Endpoint integration tests
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User
from app.modules.auth.service import (
    AuthenticationError,
    resend_email_verification_token,
    verify_email_with_token,
)
from app.modules.auth.tokens import create_email_verification_token
from app.modules.mail import SMTPDeliveryError
from app.schemas import EmailVerificationRequest
from expect import expect

settings = get_settings()


def _extract_token_from_mail_body(body_text: str) -> str:
    for line in body_text.splitlines():
        if "/verify-email?" not in line:
            continue

        token = parse_qs(urlparse(line.strip()).query).get("token")
        if token:
            return token[0]

    raise AssertionError("Verification token link not found in body_text")


def _extract_verification_link_from_mail_body(body_text: str) -> str:
    for line in body_text.splitlines():
        if "/verify-email?" in line:
            return line.strip()

    raise AssertionError("Verification link not found in body_text")


@pytest.mark.asyncio
async def test_create_email_verification_token() -> None:
    """Test creating an email verification token.

    Verifies that the token creation function generates a valid JWT token
    with the correct structure, user_id, email, and token type. Ensures
    that the expiration time is set correctly according to configuration.
    """
    # Arrange
    user_id = uuid4()
    email = "test@example.com"

    # Act
    token, expires_in = create_email_verification_token(user_id, email)

    # Assert - Token structure
    expect(token).is_not_none()
    expect(isinstance(token, str)).to_be_true()
    expect(expires_in).equal(settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60)

    # Assert - Token payload
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    expect(str(user_id)).equal(payload["user_id"])
    expect(email).equal(payload["email"])
    expect(payload["type"]).equal("email_verification")


@pytest.mark.asyncio
async def test_verify_email_with_token_success(
    db_session: AsyncSession, test_user_data: dict, verified_user: User
) -> None:
    """Test verifying email with valid token.

    Verifies that the email verification process correctly updates the user's
    email verification status and sets the timestamp when an unverified user's
    email is verified using a valid token.
    """
    # Arrange - Create unverified user
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    token, _ = create_email_verification_token(verified_user.id, verified_user.email)

    # Act
    result = await verify_email_with_token(db_session, token)

    # Assert
    expect(result.email_verified).to_be_true()
    expect(result.verified_at).is_not_none()


@pytest.mark.asyncio
async def test_verify_email_with_expired_token(
    db_session: AsyncSession, verified_user: User
) -> None:
    """Test verifying email with expired token.

    Ensures that attempting to verify an email with a token that has
    expired raises an AuthenticationError with an appropriate message.
    """
    # Arrange - Create expired token
    user_id = verified_user.id
    email = verified_user.email
    expire = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired

    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire,
        "type": "email_verification",
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Act & Assert
    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, expired_token)


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token(db_session: AsyncSession) -> None:
    """Test verifying email with invalid token.

    Ensures that attempting to verify an email with an invalid token
    raises an AuthenticationError with an appropriate error message.
    """
    # Act & Assert
    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, "invalid-token")


@pytest.mark.asyncio
async def test_verify_email_with_wrong_token_type(
    db_session: AsyncSession, verified_user: User
) -> None:
    """Test verifying email with wrong token type (e.g., access token).

    Verifies that using an access token instead of an email verification token
    results in an AuthenticationError, preventing token type confusion attacks.
    """
    # Arrange - Create access token instead of email verification token
    from app.modules.auth.tokens import create_access_token

    access_token, _ = create_access_token(verified_user.id, verified_user.email)

    # Act & Assert
    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, access_token)


@pytest.mark.asyncio
async def test_verify_email_with_nonexistent_user(db_session: AsyncSession) -> None:
    """Test verifying email when user doesn't exist.

    Ensures that attempting to verify an email for a non-existent user
    raises an AuthenticationError with a user not found message.
    """
    # Arrange
    fake_user_id = uuid4()
    token, _ = create_email_verification_token(fake_user_id, "fake@example.com")

    # Act & Assert
    with pytest.raises(AuthenticationError, match="User not found"):
        await verify_email_with_token(db_session, token)


@pytest.mark.asyncio
async def test_resend_email_verification_token_success(
    db_session: AsyncSession, verified_user: User
) -> None:
    """Test resending verification token for unverified user.

    Verifies that the resend token function generates a new valid token
    with the correct expiration time for an unverified user's email.
    """
    # Arrange - Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    # Act
    token, expires_in, username = await resend_email_verification_token(
        db_session, verified_user.email
    )

    # Assert
    expect(token).is_not_none()
    expect(isinstance(token, str)).to_be_true()
    expect(expires_in).equal(settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60)
    expect(username).equal(verified_user.username)


@pytest.mark.asyncio
async def test_resend_email_verification_token_already_verified(
    db_session: AsyncSession, verified_user: User
) -> None:
    """Test resending verification token when email already verified.

    Ensures that attempting to resend a verification token for an already
    verified user raises an AuthenticationError with an appropriate message.
    """
    # Act & Assert
    with pytest.raises(AuthenticationError, match="already verified"):
        await resend_email_verification_token(db_session, verified_user.email)


@pytest.mark.asyncio
async def test_resend_email_verification_token_user_not_found(db_session: AsyncSession) -> None:
    """Test resending verification token for non-existent user.

    Verifies that attempting to resend a token for a non-existent email
    raises an AuthenticationError with a user not found message.
    """
    # Act & Assert
    with pytest.raises(AuthenticationError, match="not found"):
        await resend_email_verification_token(db_session, "nonexistent@example.com")


@pytest.mark.asyncio
async def test_verify_email_endpoint_success(
    async_client, db_session: AsyncSession, verified_user: User
) -> None:
    """Test /auth/verify-email endpoint with valid token.

    Verifies that the endpoint correctly processes a valid email verification
    token and returns a success response with the verified user's email.
    """
    # Arrange - Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    token, _ = create_email_verification_token(verified_user.id, verified_user.email)

    # Act
    response = await async_client.post("/api/v1/auth/verify-email", json={"token": token})

    # Assert
    expect(response.status_code).equal(200)
    data = response.json()
    expect(data["message"]).contains("Email verified successfully")
    expect(data["email"]).equal(verified_user.email)


@pytest.mark.asyncio
async def test_verify_email_endpoint_invalid_token(async_client) -> None:
    """Test /auth/verify-email endpoint with invalid token.

    Ensures that the endpoint returns a 401 error when provided with an
    invalid token, preventing unauthorized email verification attempts.
    """
    # Act
    response = await async_client.post("/api/v1/auth/verify-email", json={"token": "invalid"})

    # Assert
    expect(response.status_code).equal(401)
    expect(response.json()["detail"]).contains("Invalid or expired")


@pytest.mark.asyncio
async def test_verify_email_endpoint_expired_token(async_client, verified_user: User) -> None:
    """Test /auth/verify-email endpoint with expired token.

    Verifies that the endpoint correctly rejects expired tokens with a
    401 error and appropriate error message.
    """
    # Arrange - Create expired token
    expire = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {
        "user_id": str(verified_user.id),
        "email": verified_user.email,
        "exp": expire,
        "type": "email_verification",
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Act
    response = await async_client.post("/api/v1/auth/verify-email", json={"token": expired_token})

    # Assert
    expect(response.status_code).equal(401)
    expect(response.json()["detail"]).contains("Invalid or expired")


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_success(
    async_client, db_session: AsyncSession, verified_user: User, sent_auth_emails
) -> None:
    """Test /auth/resend-verification-email endpoint success.

    Verifies that the endpoint generates a new verification token for an
    unverified user and returns appropriate success message.
    """
    # Arrange - Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()
    initial_mail_count = len(sent_auth_emails)

    # Act
    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    # Assert
    expect(response.status_code).equal(200)
    data = response.json()
    expect(data["message"]).contains("Verification token generated")
    expect(data["email"]).equal(verified_user.email)
    expect(data["message"]).contains("Copy this token")
    assert len(sent_auth_emails) == initial_mail_count


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_sends_mail_when_toggle_disabled(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test resend endpoint delivers email instead of returning token when toggle is disabled."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()
    initial_mail_count = len(sent_auth_emails)

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    data = response.json()
    expect(data["message"]).equal("Verification email sent. Please check your inbox.")
    assert "Copy this token" not in data["message"]
    assert len(sent_auth_emails) == initial_mail_count + 1
    delivered_mail = sent_auth_emails[-1]
    expect(delivered_mail["to"]).equal(verified_user.email)
    expect(delivered_mail["subject"]).equal("Your new verification link")
    token = _extract_token_from_mail_body(delivered_mail["body_text"])
    expect(token).is_not_none()


@pytest.mark.asyncio
async def test_resend_verification_email_uses_public_base_url_when_configured(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verification mails should prefer PUBLIC_BASE_URL over FRONTEND_URL."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "production")
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")
    monkeypatch.setattr(
        "app.modules.auth.router.settings.PUBLIC_BASE_URL", "https://nano.example.com"
    )
    monkeypatch.setattr("app.modules.auth.router.settings.APP_BASE_URL", None)

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("https")
    expect(parsed_link.netloc).equal("nano.example.com")
    expect(parsed_link.path).equal("/verify-email")
    query = parse_qs(parsed_link.query)
    expect(query.get("email")).is_none()
    token_values = query.get("token")
    expect(token_values).is_not_none()
    assert token_values is not None
    expect(token_values[0]).is_not_equal("")


@pytest.mark.asyncio
async def test_resend_verification_email_uses_app_base_url_as_middle_option(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verification mails should use APP_BASE_URL when PUBLIC_BASE_URL is not configured."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "production")
    monkeypatch.setattr("app.modules.auth.router.settings.PUBLIC_BASE_URL", None)
    monkeypatch.setattr(
        "app.modules.auth.router.settings.APP_BASE_URL", "https://app.nano.example.com"
    )
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("https")
    expect(parsed_link.netloc).equal("app.nano.example.com")
    expect(parsed_link.path).equal("/verify-email")


@pytest.mark.asyncio
async def test_resend_verification_email_falls_back_to_frontend_url_in_development(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development flow should still allow localhost FRONTEND_URL fallback."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "development")
    monkeypatch.setattr("app.modules.auth.router.settings.PUBLIC_BASE_URL", None)
    monkeypatch.setattr("app.modules.auth.router.settings.APP_BASE_URL", None)
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("http")
    expect(parsed_link.netloc).equal("localhost:5173")
    expect(parsed_link.path).equal("/verify-email")


@pytest.mark.asyncio
async def test_resend_verification_email_normalizes_host_only_public_base_url_in_development(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development flow should normalize PUBLIC_BASE_URL without schema to http://..."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "development")
    monkeypatch.setattr("app.modules.auth.router.settings.PUBLIC_BASE_URL", "141.41.42.209")
    monkeypatch.setattr("app.modules.auth.router.settings.APP_BASE_URL", None)
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("http")
    expect(parsed_link.netloc).equal("141.41.42.209")
    expect(parsed_link.path).equal("/verify-email")


@pytest.mark.asyncio
async def test_resend_verification_email_normalizes_host_port_public_base_url_in_development(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development flow should normalize schema-less host:port PUBLIC_BASE_URL values."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "development")
    monkeypatch.setattr("app.modules.auth.router.settings.PUBLIC_BASE_URL", "141.41.42.209:5173")
    monkeypatch.setattr("app.modules.auth.router.settings.APP_BASE_URL", None)
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("http")
    expect(parsed_link.netloc).equal("141.41.42.209:5173")
    expect(parsed_link.path).equal("/verify-email")


@pytest.mark.asyncio
async def test_resend_verification_email_uses_app_base_url_when_public_base_url_unset(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    sent_auth_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verification mails fall back to APP_BASE_URL when PUBLIC_BASE_URL is not set."""
    # This exercises the middle option in the PUBLIC_BASE_URL → APP_BASE_URL → FRONTEND_URL
    # resolution chain to ensure APP_BASE_URL (legacy alias) is not silently bypassed.
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.settings.ENV", "staging")
    monkeypatch.setattr("app.modules.auth.router.settings.FRONTEND_URL", "http://localhost:5173")
    monkeypatch.setattr("app.modules.auth.router.settings.PUBLIC_BASE_URL", None)
    monkeypatch.setattr(
        "app.modules.auth.router.settings.APP_BASE_URL", "https://staging.nano.example.com"
    )

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(200)
    delivered_mail = sent_auth_emails[-1]
    verification_link = _extract_verification_link_from_mail_body(delivered_mail["body_text"])

    parsed_link = urlparse(verification_link)
    expect(parsed_link.scheme).equal("https")
    expect(parsed_link.netloc).equal("staging.nano.example.com")
    expect(parsed_link.path).equal("/verify-email")
    query = parse_qs(parsed_link.query)
    expect(query.get("email")).is_none()
    token_values = query.get("token")
    expect(token_values).is_not_none()
    assert token_values is not None
    expect(token_values[0]).is_not_equal("")


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_smtp_failure_returns_safe_503(
    async_client,
    db_session: AsyncSession,
    verified_user: User,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test resend endpoint maps SMTP delivery failures to the stable 503 contract."""
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    async def mock_send_mail(_to: str, _subject: str, _body_html: str, _body_text: str) -> None:
        raise SMTPDeliveryError("mail relay timeout", attempts=3)

    monkeypatch.setattr("app.modules.auth.router.settings.AUTH_RESEND_RETURN_TOKEN", False)
    monkeypatch.setattr("app.modules.auth.router.send_mail", mock_send_mail)
    caplog.set_level("ERROR", logger="app.modules.auth.router")

    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    expect(response.status_code).equal(503)
    expect(response.json()["detail"]).equal(
        "Email delivery is currently unavailable. Please try again later."
    )

    record = next(record for record in caplog.records if record.msg == "auth_mail_delivery_failed")
    expect(record.flow_name).equal("resend_verification")
    expect(record.message_type).equal("resend_verification")
    expect(record.correlation_id).is_not_none()


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_already_verified(
    async_client, verified_user: User
) -> None:
    """Test /auth/resend-verification-email for already verified user.

    Ensures that the endpoint rejects requests for already verified users
    with a 401 error and appropriate error message.
    """
    # Act
    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    # Assert
    expect(response.status_code).equal(401)
    expect(response.json()["detail"]).contains("already verified")


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_user_not_found(async_client) -> None:
    """Test /auth/resend-verification-email for non-existent user.

    Verifies that the endpoint returns a 401 error when attempting to
    resend verification for a non-existent email address.
    """
    # Act
    response = await async_client.post(
        "/api/v1/auth/resend-verification-email", json={"email": "nonexistent@example.com"}
    )

    # Assert
    expect(response.status_code).equal(401)
    expect(response.json()["detail"]).contains("not found")


@pytest.mark.asyncio
async def test_verify_email_integration_then_login_success(
    async_client, db_session: AsyncSession, test_user_data: dict
) -> None:
    """Integration test: Register user, verify email, then login successfully.

    This tests the complete email verification flow end-to-end:
    1. User registration
    2. Attempt login before verification (should fail)
    3. Email verification via token
    4. Successful login after verification
    """
    # Step 1: Register user
    # Act
    response = await async_client.post("/api/v1/auth/register", json=test_user_data)

    # Assert
    expect(response.status_code).equal(201)
    user_data = response.json()
    expect(user_data["email_verified"]).to_be_false()

    # Step 2: Try to login before verification (should fail)
    # Arrange
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }

    # Act
    response = await async_client.post("/api/v1/auth/login", json=login_data)

    # Assert
    expect(response.status_code).equal(403)
    expect(response.json()["detail"].lower()).contains("not verified")

    # Step 3: Generate verification token and verify email
    # In production, this token would be sent via email
    from sqlalchemy import select

    # Arrange
    query = select(User).where(User.email == test_user_data["email"].lower())
    result = await db_session.execute(query)
    user = result.scalar_one()

    token, _ = create_email_verification_token(user.id, user.email)

    # Act
    response = await async_client.post("/api/v1/auth/verify-email", json={"token": token})

    # Assert
    expect(response.status_code).equal(200)
    expect(response.json()["message"].lower()).contains("successfully")

    # Step 4: Login should now succeed
    # Act
    response = await async_client.post("/api/v1/auth/login", json=login_data)

    # Assert
    expect(response.status_code).equal(200)
    tokens = response.json()
    expect(tokens).has_keys("access_token", "refresh_token")
