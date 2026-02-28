"""
Password hashing and verification utilities.

This module implements secure password hashing using bcrypt with a minimum cost factor of 12.
The implementation follows OWASP guidelines for password storage and includes:

- bcrypt hashing with cost factor 12 (2^12 = 4096 iterations)
- Constant-time comparison via passlib to prevent timing attacks
- SHA256 pre-hashing for passwords exceeding bcrypt's 72-byte limit
- No plain-text password storage or logging

Security Properties:
- Passwords are hashed using bcrypt with salt (automatically handled by bcrypt)
- Verification uses constant-time comparison (handled by passlib internally)
- Failed verifications do not leak information about password correctness
- No passwords are stored in logs or error messages
"""

import hashlib
import logging
from typing import Final

from passlib.context import CryptContext

# Configure logging (passwords will NEVER be logged)
logger = logging.getLogger(__name__)

# Bcrypt cost factor
# 12 rounds = 2^12 = 4096 iterations (meets OWASP minimum of 10)
# Higher values increase security but also computation time
BCRYPT_ROUNDS: Final[int] = 12

# Configure bcrypt-only context (no fallbacks for production security)
# passlib's bcrypt implementation uses constant-time comparison internally
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_ROUNDS,
)

# Bcrypt has a 72-byte password limit
BCRYPT_MAX_PASSWORD_BYTES: Final[int] = 72


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salting.

    For passwords longer than 72 bytes, SHA256 pre-hashing is applied
    to ensure compatibility with bcrypt's length limitation.

    Security notes:
    - bcrypt automatically generates a unique salt for each password
    - Cost factor of 12 provides strong security against brute-force
    - The returned hash includes the salt and cost factor (bcrypt format)

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hash string (60 chars) in format: $2b$12$[22-char salt][31-char hash]

    Raises:
        ValueError: If password is empty or exceeds reasonable length limits
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) > 1000:  # Sanity check to prevent DoS
        raise ValueError("Password exceeds maximum length")

    # Apply SHA256 pre-hashing for long passwords (bcrypt 72-byte limit)
    password_to_hash = password
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        password_to_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        logger.debug("Applied SHA256 pre-hashing for long password")

    try:
        hashed = pwd_context.hash(password_to_hash)
        return hashed
    except Exception as e:
        # Log error without exposing password
        logger.error(f"Password hashing failed: {type(e).__name__}")
        raise RuntimeError("Failed to hash password") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    This function uses constant-time comparison (via passlib) to prevent
    timing attacks that could leak information about password correctness.

    The same SHA256 pre-hashing is applied if the password exceeds 72 bytes,
    ensuring consistency with the hashing process.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches hash, False otherwise

    Note:
        - Returns False for any errors (invalid hash format, etc.)
        - Does not raise exceptions to prevent information leakage
        - Uses constant-time comparison internally (passlib)
    """
    if not plain_password or not hashed_password:
        return False

    try:
        # Apply same pre-hashing logic as hash_password
        password_to_verify = plain_password
        if len(plain_password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            password_to_verify = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()

        # passlib's verify() uses constant-time comparison internally
        return pwd_context.verify(password_to_verify, hashed_password)
    except Exception:
        # Return False for any errors (invalid hash, etc.)
        # Do not log password or expose error details
        return False


def get_password_hash_info(hashed_password: str) -> dict[str, str | int | None]:
    """
    Extract metadata from a bcrypt password hash.

    Useful for diagnostics and migration planning (e.g., identifying
    hashes that need to be upgraded to higher cost factors).

    Args:
        hashed_password: Bcrypt hash string

    Returns:
        Dictionary with keys:
        - scheme: Hashing scheme (e.g., "bcrypt")
        - rounds: Cost factor (e.g., 12)
        - valid: Whether hash format is valid

    Example:
        >>> info = get_password_hash_info("$2b$12$...")
        >>> print(info)
        {'scheme': 'bcrypt', 'rounds': 12, 'valid': True}
    """
    try:
        hash_info = pwd_context.identify(hashed_password, resolve=True)
        if hash_info:
            # Extract rounds from bcrypt hash (format: $2b$12$...)
            parts = hashed_password.split("$")
            rounds = int(parts[2]) if len(parts) >= 3 else None
            return {
                "scheme": hash_info,
                "rounds": rounds,
                "valid": True,
            }
    except Exception:
        pass

    return {"scheme": None, "rounds": None, "valid": False}
