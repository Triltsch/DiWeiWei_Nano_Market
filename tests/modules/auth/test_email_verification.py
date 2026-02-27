"""Tests for email verification functionality"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
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

settings = get_settings()


@pytest.mark.asyncio
async def test_create_email_verification_token():
    """Test creating an email verification token"""
    user_id = uuid4()
    email = "test@example.com"

    token, expires_in = create_email_verification_token(user_id, email)

    assert token is not None
    assert isinstance(token, str)
    assert expires_in == settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60

    # Verify token structure
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert str(user_id) == payload["user_id"]
    assert email == payload["email"]
    assert payload["type"] == "email_verification"


@pytest.mark.asyncio
async def test_verify_email_with_token_success(
    db_session: AsyncSession, test_user_data: dict, verified_user: User
):
    """Test verifying email with valid token"""
    # Create token for unverified user
    token, _ = create_email_verification_token(verified_user.id, verified_user.email)

    # Create an unverified user by updating the one we have
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    # Verify the email
    result = await verify_email_with_token(db_session, token)

    assert result.email_verified is True
    assert result.verified_at is not None


@pytest.mark.asyncio
async def test_verify_email_with_expired_token(db_session: AsyncSession, verified_user: User):
    """Test verifying email with expired token"""
    # Create expired token
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

    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, expired_token)


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token(db_session: AsyncSession):
    """Test verifying email with invalid token"""
    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, "invalid-token")


@pytest.mark.asyncio
async def test_verify_email_with_wrong_token_type(db_session: AsyncSession, verified_user: User):
    """Test verifying email with wrong token type (e.g., access token)"""
    # Create access token instead of email verification token
    from app.modules.auth.tokens import create_access_token

    access_token, _ = create_access_token(verified_user.id, verified_user.email)

    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await verify_email_with_token(db_session, access_token)


@pytest.mark.asyncio
async def test_verify_email_with_nonexistent_user(db_session: AsyncSession):
    """Test verifying email when user doesn't exist"""
    # Create token for non-existent user
    fake_user_id = uuid4()
    token, _ = create_email_verification_token(fake_user_id, "fake@example.com")

    with pytest.raises(AuthenticationError, match="User not found"):
        await verify_email_with_token(db_session, token)


@pytest.mark.asyncio
async def test_resend_email_verification_token_success(
    db_session: AsyncSession, verified_user: User
):
    """Test resending verification token for unverified user"""
    # Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    token, expires_in = await resend_email_verification_token(db_session, verified_user.email)

    assert token is not None
    assert isinstance(token, str)
    assert expires_in == settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60


@pytest.mark.asyncio
async def test_resend_email_verification_token_already_verified(
    db_session: AsyncSession, verified_user: User
):
    """Test resending verification token when email already verified"""
    with pytest.raises(AuthenticationError, match="already verified"):
        await resend_email_verification_token(db_session, verified_user.email)


@pytest.mark.asyncio
async def test_resend_email_verification_token_user_not_found(db_session: AsyncSession):
    """Test resending verification token for non-existent user"""
    with pytest.raises(AuthenticationError, match="not found"):
        await resend_email_verification_token(db_session, "nonexistent@example.com")


@pytest.mark.asyncio
async def test_verify_email_endpoint_success(
    client: TestClient, db_session: AsyncSession, verified_user: User
):
    """Test /auth/verify-email endpoint with valid token"""
    # Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    # Create valid token
    token, _ = create_email_verification_token(verified_user.id, verified_user.email)

    response = client.post("/api/v1/auth/verify-email", json={"token": token})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Email verified successfully. You can now login."
    assert data["email"] == verified_user.email


@pytest.mark.asyncio
async def test_verify_email_endpoint_invalid_token(client: TestClient):
    """Test /auth/verify-email endpoint with invalid token"""
    response = client.post("/api/v1/auth/verify-email", json={"token": "invalid"})

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_email_endpoint_expired_token(client: TestClient, verified_user: User):
    """Test /auth/verify-email endpoint with expired token"""
    # Create expired token
    expire = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {
        "user_id": str(verified_user.id),
        "email": verified_user.email,
        "exp": expire,
        "type": "email_verification",
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = client.post("/api/v1/auth/verify-email", json={"token": expired_token})

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_success(
    client: TestClient, db_session: AsyncSession, verified_user: User
):
    """Test /auth/resend-verification-email endpoint success"""
    # Mark user as unverified
    verified_user.email_verified = False
    verified_user.verified_at = None
    db_session.add(verified_user)
    await db_session.commit()

    response = client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    assert response.status_code == 200
    data = response.json()
    assert "Verification token generated" in data["message"]
    assert data["email"] == verified_user.email
    # In MVP mode, token is returned in message for testing
    assert "Copy this token" in data["message"]


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_already_verified(
    client: TestClient, verified_user: User
):
    """Test /auth/resend-verification-email for already verified user"""
    response = client.post(
        "/api/v1/auth/resend-verification-email", json={"email": verified_user.email}
    )

    assert response.status_code == 401
    assert "already verified" in response.json()["detail"]


@pytest.mark.asyncio
async def test_resend_verification_email_endpoint_user_not_found(client: TestClient):
    """Test /auth/resend-verification-email for non-existent user"""
    response = client.post(
        "/api/v1/auth/resend-verification-email", json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 401
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_email_integration_then_login_success(
    client: TestClient, db_session: AsyncSession, test_user_data: dict
):
    """
    Integration test: Register user, verify email, then login successfully

    This tests the complete email verification flow end-to-end.
    """
    # Step 1: Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_data = response.json()
    assert not user_data["email_verified"]

    # Step 2: Try to login before verification (should fail)
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 403
    assert "not verified" in response.json()["detail"].lower()

    # Step 3: Generate verification token and verify email
    # In production, this token would be sent via email
    from sqlalchemy import select

    query = select(User).where(User.email == test_user_data["email"].lower())
    result = await db_session.execute(query)
    user = result.scalar_one()

    token, _ = create_email_verification_token(user.id, user.email)

    response = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert "successfully" in response.json()["message"].lower()

    # Step 4: Login should now succeed
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
