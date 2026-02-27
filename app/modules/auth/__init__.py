"""Authentication module - handles user registration, login, and JWT tokens"""

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

__all__ = [
    "register_user",
    "authenticate_user",
    "record_failed_login",
    "get_user_by_id",
    "verify_user_email",
    "refresh_access_token",
    "AuthenticationError",
    "InvalidCredentialsError",
    "UserAlreadyExistsError",
    "AccountLockedError",
    "AccountNotVerifiedError",
]
