"""Password hashing and verification utilities"""

import hashlib

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
    # Pre-hash if password is longer than 72 bytes (bcrypt limit)
    if USE_BCRYPT and len(password.encode()) > 72:
        password = hashlib.sha256(password.encode()).hexdigest()

    return pwd_context.hash(password)


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
        return False
