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


def calculate_password_strength(password: str) -> dict[str, str | int | list[str]]:
    """
    Calculate password strength and provide feedback.

    Returns a strength score (0-100) and suggestions for improvement.
    This is designed to provide user-friendly feedback in the frontend.

    Scoring criteria:
    - Length: Up to 40 points (8+ chars = 20, 12+ chars = 30, 16+ chars = 40)
    - Character variety: Up to 40 points (lowercase, uppercase, digits, special)
    - Complexity: Up to 20 points (no common patterns, no repeating chars)

    Args:
        password: Password to evaluate

    Returns:
        Dictionary with keys:
        - score: Integer 0-100
        - strength: String ("weak", "fair", "good", "strong", "very_strong")
        - suggestions: List of improvement suggestions
        - meets_policy: Boolean indicating if password meets minimum policy
    """
    if not password:
        return {
            "score": 0,
            "strength": "weak",
            "suggestions": ["Password cannot be empty"],
            "meets_policy": False,
        }

    score = 0
    suggestions = []

    # Length scoring (up to 40 points)
    length = len(password)
    if length >= 16:
        score += 40
    elif length >= 12:
        score += 30
    elif length >= 8:
        score += 20
    else:
        score += length * 2
        suggestions.append(f"Use at least {settings.MIN_PASSWORD_LENGTH} characters")

    # Character variety (up to 40 points, 10 per category)
    has_lowercase = bool(re.search(r"[a-z]", password))
    has_uppercase = bool(re.search(r"[A-Z]", password))
    has_digit = bool(re.search(r"[0-9]", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\;'/~`]", password))

    if has_lowercase:
        score += 10
    else:
        suggestions.append("Add lowercase letters")

    if has_uppercase:
        score += 10
    else:
        suggestions.append("Add uppercase letters")

    if has_digit:
        score += 10
    else:
        suggestions.append("Add numbers")

    if has_special:
        score += 10
    else:
        suggestions.append("Add special characters (!@#$%^&* etc.)")

    # Complexity bonus (up to 20 points)
    # Check for common patterns
    common_patterns = [
        r"123",
        r"abc",
        r"qwerty",
        r"password",
        r"admin",
        r"user",
        r"pass",
    ]
    has_common = any(re.search(pattern, password.lower()) for pattern in common_patterns)
    if has_common:
        suggestions.append("Avoid common words and sequences")
    else:
        score += 10

    # Check for excessive repeating characters
    has_repeating = bool(re.search(r"(.)\1{2,}", password))
    if has_repeating:
        suggestions.append("Avoid repeating characters (e.g., 'aaa', '111')")
    else:
        score += 10

    # Determine strength label
    if score >= 80:
        strength = "very_strong"
    elif score >= 60:
        strength = "strong"
    elif score >= 40:
        strength = "good"
    elif score >= 20:
        strength = "fair"
    else:
        strength = "weak"

    # Check if meets policy
    meets_policy, _ = validate_password_strength(password)

    return {
        "score": min(score, 100),
        "strength": strength,
        "suggestions": suggestions,
        "meets_policy": meets_policy,
    }


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
