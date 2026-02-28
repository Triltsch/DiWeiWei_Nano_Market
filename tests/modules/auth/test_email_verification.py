"""Tests for email verification functionality.

This module contains comprehensive tests for the email verification system, including:
- Token creation and validation
- Email verification workflows
- Token expiration and error handling
- Endpoint integration tests
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User
from app.modules.auth.service import (
    AuthenticationError,
    resend_email_verification_token,
    verify_email_with_token,
)
from app.modules.auth.tokens import create_email_verification_token
from app.schemas import EmailVerificationRequest
from expect import expect

settings = get_settings()


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
    token, expires_in = await resend_email_verification_token(db_session, verified_user.email)

    # Assert
    expect(token).is_not_none()
    expect(isinstance(token, str)).to_be_true()
    expect(expires_in).equal(settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60)


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
    async_client, db_session: AsyncSession, verified_user: User
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
