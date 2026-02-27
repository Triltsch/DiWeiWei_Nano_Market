"""Authentication service business logic"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User, UserRole, UserStatus
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.tokens import create_access_token, create_refresh_token, verify_token
from app.modules.auth.validators import (
    validate_email,
    validate_password_strength,
    validate_username,
)
from app.schemas import TokenResponse, UserRegister, UserResponse

settings = get_settings()


class AuthenticationError(Exception):
    """Base authentication error"""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password"""

    pass


class UserAlreadyExistsError(AuthenticationError):
    """User already exists"""

    pass


class AccountLockedError(AuthenticationError):
    """Account is locked due to too many login attempts"""

    pass


class AccountNotVerifiedError(AuthenticationError):
    """Account email not verified"""

    pass


async def register_user(db_session: AsyncSession, user_data: UserRegister) -> UserResponse:
    """
    Register a new user.

    Args:
        db_session: Database session
        user_data: Registration data

    Returns:
        UserResponse: Created user data

    Raises:
        UserAlreadyExistsError: If email or username already exists
        AuthenticationError: If validation fails
    """
    # Validate input
    is_valid, error_msg = validate_email(user_data.email)
    if not is_valid:
        raise AuthenticationError(error_msg)

    is_valid, error_msg = validate_username(user_data.username)
    if not is_valid:
        raise AuthenticationError(error_msg)

    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise AuthenticationError(error_msg)

    # Check if email already exists (case-insensitive)
    email_lower = user_data.email.lower()
    query = select(User).where(User.email == email_lower)
    result = await db_session.execute(query)
    if result.scalar_one_or_none() is not None:
        raise UserAlreadyExistsError("Email already registered")

    # Check if username already exists
    query = select(User).where(User.username == user_data.username)
    result = await db_session.execute(query)
    if result.scalar_one_or_none() is not None:
        raise UserAlreadyExistsError("Username already taken")

    # Create new user
    user = User(
        email=email_lower,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        bio=user_data.bio,
        preferred_language=user_data.preferred_language,
        status=UserStatus.ACTIVE,
        role=UserRole.CONSUMER,
        email_verified=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return UserResponse.model_validate(user)


async def authenticate_user(
    db_session: AsyncSession, email: str, password: str
) -> tuple[UserResponse, TokenResponse]:
    """
    Authenticate a user and return tokens.

    Args:
        db_session: Database session
        email: User email
        password: User password

    Returns:
        Tuple of (UserResponse, TokenResponse)

    Raises:
        InvalidCredentialsError: If credentials are invalid
        AccountLockedError: If account is locked
        AccountNotVerifiedError: If email not verified
    """
    email_lower = email.lower()

    # Find user by email
    query = select(User).where(User.email == email_lower)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsError("Invalid email or password")

    # Check if account is locked before password verification
    if user.locked_until:
        # Handle both naive and aware datetimes
        locked_until = user.locked_until
        now = datetime.now(timezone.utc)
        if locked_until.tzinfo is None:
            # If locked_until is naive, make it aware
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > now:
            raise AccountLockedError("Account is locked due to too many failed login attempts")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")

    # Check if email is verified
    if not user.email_verified:
        raise AccountNotVerifiedError("Email not verified. Please verify your email first.")

    # Check if account is active
    if user.status != UserStatus.ACTIVE:
        raise AuthenticationError(f"Account is {user.status}")

    # Reset login attempts and generate tokens
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create tokens
    access_token, access_expires_in = create_access_token(user.id, user.email)
    refresh_token, refresh_expires_in = create_refresh_token(user.id, user.email)

    user_response = UserResponse.model_validate(user)
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_expires_in,
    )

    return user_response, token_response


async def record_failed_login(db_session: AsyncSession, email: str) -> None:
    """
    Record a failed login attempt and lock account if needed.

    Args:
        db_session: Database session
        email: User email
    """
    email_lower = email.lower()

    query = select(User).where(User.email == email_lower)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        return

    user.login_attempts += 1

    if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
        )

    db_session.add(user)
    await db_session.commit()


async def get_user_by_id(db_session: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def verify_user_email(db_session: AsyncSession, user_id: UUID) -> User:
    """
    Mark user email as verified.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        Updated user

    Raises:
        AuthenticationError: If user not found
    """
    user = await get_user_by_id(db_session, user_id)

    if user is None:
        raise AuthenticationError("User not found")

    user.email_verified = True
    user.verified_at = datetime.now(timezone.utc)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


async def refresh_access_token(db_session: AsyncSession, refresh_token: str) -> TokenResponse:
    """
    Create a new access token from a refresh token.

    Args:
        db_session: Database session
        refresh_token: Refresh token

    Returns:
        TokenResponse with new access token

    Raises:
        AuthenticationError: If refresh token is invalid
    """
    token_data = verify_token(refresh_token, token_type="refresh")

    if token_data is None:
        raise AuthenticationError("Invalid or expired refresh token")

    # Get user to ensure they still exist and are active
    user = await get_user_by_id(db_session, token_data.user_id)

    if user is None or user.status != UserStatus.ACTIVE:
        raise AuthenticationError("User not found or account is inactive")

    # Create new access token
    access_token, access_expires_in = create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_expires_in,
    )
