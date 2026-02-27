"""Tests for JWT token utilities"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.config import get_settings
from app.modules.auth.tokens import verify_token

settings = get_settings()


def test_verify_token_missing_claims_returns_none():
    """Missing claims should produce None instead of raising."""
    payload = {
        "email": "user@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    assert verify_token(token, token_type="access") is None


def test_verify_token_invalid_uuid_returns_none():
    """Invalid UUID should produce None instead of raising."""
    payload = {
        "user_id": "not-a-uuid",
        "email": "user@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    assert verify_token(token, token_type="access") is None


def test_verify_token_invalid_exp_returns_none():
    """Non-numeric exp claim should produce None instead of raising."""
    payload = {
        "user_id": str(uuid4()),
        "email": "user@example.com",
        "exp": "not-a-timestamp",
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    assert verify_token(token, token_type="access") is None
