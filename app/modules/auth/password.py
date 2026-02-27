"""Password hashing and verification utilities"""

import hashlib
import hmac
import os

from passlib.context import CryptContext

# Configure bcrypt context with fallback to plaintext (for testing only)
# In production, ensure bcrypt backend is properly installed
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    # Test if bcrypt works
    _ = pwd_context.hash("test_password")
    USE_BCRYPT = True
except Exception:
    # Fallback for environments where bcrypt has issues
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    USE_BCRYPT = False

# Global salt for fallback hashing - in production, should be configured
_FALLBACK_SALT = os.environ.get("PASSWORD_SALT", "default-salt-change-in-production").encode()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with SHA256 pre-hashing for long passwords.

    Note: bcrypt has a 72-byte limit for passwords. Passwords longer than this
    are first hashed with SHA256 before being passed to bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    try:
        # Pre-hash if password is longer than 72 bytes (bcrypt limit)
        if USE_BCRYPT and len(password.encode()) > 72:
            password = hashlib.sha256(password.encode()).hexdigest()

        return pwd_context.hash(password)
    except Exception:
        # Fallback to PBKDF2 if passlib fails
        password_bytes = password.encode()
        hashed = hashlib.pbkdf2_hmac("sha256", password_bytes, _FALLBACK_SALT, 100000)
        return hashlib.sha256(hashed).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Apply same pre-hashing if needed
        if USE_BCRYPT and len(plain_password.encode()) > 72:
            plain_password = hashlib.sha256(plain_password.encode()).hexdigest()

        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Try fallback comparison
        password_bytes = plain_password.encode()
        computed_hash = hashlib.pbkdf2_hmac("sha256", password_bytes, _FALLBACK_SALT, 100000)
        computed_hash_str = hashlib.sha256(computed_hash).hexdigest()

        # Use constant-time comparison
        return hmac.compare_digest(computed_hash_str, hashed_password)
