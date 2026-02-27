"""Integration tests for authentication flows with PostgreSQL.

These tests require Docker PostgreSQL to be running and TEST_DB_URL to be set.
They validate real database interactions including:
- Full registration and login flow
- Account lockout mechanism
- Email verification constraints
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import (
    AccountLockedError,
    AccountNotVerifiedError,
    authenticate_user,
    record_failed_login,
    register_user,
    verify_user_email,
)
from app.schemas import UserRegister


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_full_registration_and_login_flow(
    db_session: AsyncSession, test_user_data: dict
):
    """Test complete user registration and login flow with real database constraints.

    This test validates:
    - User registration with password hashing
    - Email uniqueness constraint
    - Username uniqueness constraint
    - Successful login after email verification
    - Token generation
    """
    # Step 1: Register a new user
    user_data = UserRegister(**test_user_data)
    registered_user = await register_user(db_session, user_data)

    assert registered_user.email == test_user_data["email"].lower()
    assert registered_user.username == test_user_data["username"]
    assert not registered_user.email_verified

    # Step 2: Verify email in database
    await verify_user_email(db_session, registered_user.id)

    # Step 3: Authenticate and get tokens
    user_response, token_response = await authenticate_user(
        db_session, test_user_data["email"], test_user_data["password"]
    )

    assert user_response.email == test_user_data["email"].lower()
    assert token_response.access_token is not None
    assert token_response.refresh_token is not None
    assert token_response.expires_in > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_email_verification_constraint(
    db_session: AsyncSession, test_user_data: dict
):
    """Test that login fails when email is not verified.

    This test validates PostgreSQL constraint enforcement:
    - Unverified account cannot login
    - Proper error message when email not verified
    """
    # Register user but don't verify email
    user_data = UserRegister(**test_user_data)
    registered_user = await register_user(db_session, user_data)

    assert not registered_user.email_verified

    # Attempt to login with unverified email
    with pytest.raises(AccountNotVerifiedError) as exc_info:
        await authenticate_user(db_session, test_user_data["email"], test_user_data["password"])

    assert "Email not verified" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_account_lockout_mechanism(
    db_session: AsyncSession, test_user_data: dict
):
    """Test account lockout after multiple failed login attempts.

    This test validates:
    - Account locks after 5 failed attempts
    - Subsequent login attempts fail with AccountLockedError
    - Lock persists in database
    """
    # Register and verify user
    user_data = UserRegister(**test_user_data)
    registered_user = await register_user(db_session, user_data)
    await verify_user_email(db_session, registered_user.id)

    # Record 5 failed login attempts (triggering account lock)
    for _ in range(5):
        await record_failed_login(db_session, test_user_data["email"])

    # Attempt to login with correct password should fail due to lockout
    with pytest.raises(AccountLockedError) as exc_info:
        await authenticate_user(db_session, test_user_data["email"], test_user_data["password"])

    assert "Account is locked" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_email_uniqueness_constraint(
    db_session: AsyncSession, test_user_data: dict
):
    """Test email uniqueness constraint in PostgreSQL.

    This test validates:
    - Case-insensitive email uniqueness
    - Duplicate email registration fails
    - Proper error message
    """
    # Register first user
    user_data = UserRegister(**test_user_data)
    await register_user(db_session, user_data)

    # Attempt to register duplicate email (different case)
    from app.modules.auth.service import UserAlreadyExistsError

    duplicate_user_data = UserRegister(**test_user_data)
    duplicate_user_data.email = test_user_data["email"].upper()  # Different case

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await register_user(db_session, duplicate_user_data)

    assert "Email already registered" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_username_uniqueness_constraint(
    db_session: AsyncSession, test_user_data: dict
):
    """Test username uniqueness constraint in PostgreSQL.

    This test validates:
    - Username uniqueness
    - Duplicate username registration fails
    - Proper error message
    """
    from app.modules.auth.service import UserAlreadyExistsError

    # Register first user
    user_data = UserRegister(**test_user_data)
    await register_user(db_session, user_data)

    # Attempt to register duplicate username
    duplicate_user_data = UserRegister(**test_user_data)
    duplicate_user_data.email = "different@example.com"
    duplicate_user_data.username = test_user_data["username"]  # Same username

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await register_user(db_session, duplicate_user_data)

    assert "Username already taken" in str(exc_info.value)
