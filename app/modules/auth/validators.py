"""Validation utilities for user data"""

import re
from typing import Tuple

from app.config import get_settings

settings = get_settings()


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to policy.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters"

    if settings.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if settings.REQUIRE_DIGIT and not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"

    if settings.REQUIRE_SPECIAL_CHAR and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 20:
        return False, "Username must be at most 20 characters"

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic email validation (pydantic EmailStr will do more thorough validation)
    if not email or "@" not in email:
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email is too long"

    return True, ""
