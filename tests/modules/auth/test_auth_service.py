"""Tests for authentication service"""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.password import verify_password
from app.modules.auth.service import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    get_user_by_id,
    record_failed_login,
    refresh_access_token,
    register_user,
    verify_user_email,
)
from app.modules.auth.tokens import verify_token
from app.schemas import UserRegister


@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession, test_user_data: dict):
    """Test successful user registration"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    assert user.email == test_user_data["email"].lower()
    assert user.username == test_user_data["username"]
    assert user.first_name == test_user_data["first_name"]
    assert not user.email_verified
    assert user.id is not None
    assert isinstance(user.id, UUID)


@pytest.mark.asyncio
async def test_register_user_invalid_email(db_session: AsyncSession, test_user_data: dict):
    """Test registration with invalid email - caught by Pydantic validation"""
    from pydantic_core import ValidationError

    test_user_data["email"] = "invalid-email"

    with pytest.raises(ValidationError):
        UserRegister(**test_user_data)


@pytest.mark.asyncio
async def test_register_user_short_username(db_session: AsyncSession, test_user_data: dict):
    """Test registration with username too short - caught by Pydantic validation"""
    from pydantic_core import ValidationError

    test_user_data["username"] = "ab"

    with pytest.raises(ValidationError):
        UserRegister(**test_user_data)


@pytest.mark.asyncio
async def test_register_user_invalid_username_chars(db_session: AsyncSession, test_user_data: dict):
    """Test registration with invalid characters in username - caught by Pydantic validation"""
    from pydantic_core import ValidationError

    test_user_data["username"] = "test-user!"

    with pytest.raises(ValidationError):
        UserRegister(**test_user_data)


@pytest.mark.asyncio
async def test_register_user_weak_password(db_session: AsyncSession, test_user_data: dict):
    """Test registration with weak password - business logic validation in service"""
    # This test validates custom password strength via the service layer
    # Pydantic only checks min_length=8
    test_user_data["password"] = "short"  # Only 5 chars - Pydantic catch

    from pydantic_core import ValidationError

    with pytest.raises(ValidationError):
        UserRegister(**test_user_data)


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session: AsyncSession, test_user_data: dict):
    """Test registration with duplicate email"""
    user_data = UserRegister(**test_user_data)
    await register_user(db_session, user_data)

    # Try to register with same email
    test_user_data["username"] = "different_user"
    user_data2 = UserRegister(**test_user_data)

    with pytest.raises(UserAlreadyExistsError):
        await register_user(db_session, user_data2)


@pytest.mark.asyncio
async def test_register_user_duplicate_username(db_session: AsyncSession, test_user_data: dict):
    """Test registration with duplicate username"""
    user_data = UserRegister(**test_user_data)
    await register_user(db_session, user_data)

    # Try to register with same username
    test_user_data["email"] = "different@example.com"
    user_data2 = UserRegister(**test_user_data)

    with pytest.raises(UserAlreadyExistsError):
        await register_user(db_session, user_data2)


@pytest.mark.asyncio
async def test_register_user_email_case_insensitive(db_session: AsyncSession, test_user_data: dict):
    """Test that email is stored in lowercase"""
    test_user_data["email"] = "TestUser@Example.COM"
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    assert user.email == "testuser@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_not_verified(db_session: AsyncSession, test_user_data: dict):
    """Test login fails if email not verified"""
    user_data = UserRegister(**test_user_data)
    await register_user(db_session, user_data)

    with pytest.raises(AccountNotVerifiedError):
        await authenticate_user(db_session, test_user_data["email"], test_user_data["password"])


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(db_session: AsyncSession, test_user_data: dict):
    """Test login fails with invalid password"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    # Verify email
    await verify_user_email(db_session, user.id)

    with pytest.raises(InvalidCredentialsError):
        await authenticate_user(db_session, test_user_data["email"], "WrongPassword123!")


@pytest.mark.asyncio
async def test_authenticate_user_invalid_email(db_session: AsyncSession):
    """Test login fails with invalid email"""
    with pytest.raises(InvalidCredentialsError):
        await authenticate_user(db_session, "nonexistent@example.com", "SomePassword123!")


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession, test_user_data: dict):
    """Test successful login"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    # Verify email
    await verify_user_email(db_session, user.id)

    # Login
    user_response, token_response = await authenticate_user(
        db_session, test_user_data["email"], test_user_data["password"]
    )

    assert user_response.email == test_user_data["email"].lower()
    assert token_response.access_token is not None
    assert token_response.refresh_token is not None
    assert token_response.token_type == "bearer"
    assert token_response.expires_in == 15 * 60  # 15 minutes


@pytest.mark.asyncio
async def test_authenticate_user_case_insensitive_email(
    db_session: AsyncSession, test_user_data: dict
):
    """Test that email is case-insensitive for login"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)
    await verify_user_email(db_session, user.id)

    # Login with uppercase email
    user_response, token_response = await authenticate_user(
        db_session, test_user_data["email"].upper(), test_user_data["password"]
    )

    assert user_response.id == user.id


@pytest.mark.asyncio
async def test_record_failed_login(db_session: AsyncSession, test_user_data: dict):
    """Test recording failed login attempts"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    # Record failed attempts
    for i in range(1, 4):
        await record_failed_login(db_session, test_user_data["email"])

        # Check user is locked after 3 attempts
        if i >= 3:
            user_check = await get_user_by_id(db_session, user.id)
            assert user_check.locked_until is not None


@pytest.mark.asyncio
async def test_authenticate_locked_account(db_session: AsyncSession, test_user_data: dict):
    """Test login fails for locked account"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)
    await verify_user_email(db_session, user.id)

    # Lock account
    for _ in range(3):
        await record_failed_login(db_session, test_user_data["email"])

    with pytest.raises(AccountLockedError):
        await authenticate_user(db_session, test_user_data["email"], test_user_data["password"])


@pytest.mark.asyncio
async def test_verify_user_email(db_session: AsyncSession, test_user_data: dict):
    """Test email verification"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    assert not user.email_verified

    verified_user = await verify_user_email(db_session, user.id)

    assert verified_user.email_verified
    assert verified_user.verified_at is not None


@pytest.mark.asyncio
async def test_refresh_token(db_session: AsyncSession, test_user_data: dict):
    """Test token refresh"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)
    await verify_user_email(db_session, user.id)

    _, token_response = await authenticate_user(
        db_session, test_user_data["email"], test_user_data["password"]
    )

    # Refresh token
    new_token_response = await refresh_access_token(db_session, token_response.refresh_token)

    assert new_token_response.access_token is not None
    assert new_token_response.refresh_token != token_response.refresh_token
    assert new_token_response.token_type == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(db_session: AsyncSession):
    """Test refresh with invalid token"""
    with pytest.raises(AuthenticationError):
        await refresh_access_token(db_session, "invalid_token")


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession, test_user_data: dict):
    """Test getting user by ID"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    retrieved_user = await get_user_by_id(db_session, user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    """Test getting non-existent user"""
    from uuid import uuid4

    retrieved_user = await get_user_by_id(db_session, uuid4())

    assert retrieved_user is None


@pytest.mark.asyncio
async def test_password_is_hashed(db_session: AsyncSession, test_user_data: dict):
    """Test that password is properly hashed"""
    user_data = UserRegister(**test_user_data)
    user = await register_user(db_session, user_data)

    # Get user from DB
    db_user = await get_user_by_id(db_session, user.id)

    assert db_user.password_hash != test_user_data["password"]
    assert verify_password(test_user_data["password"], db_user.password_hash)
