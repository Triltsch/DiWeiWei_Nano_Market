"""JWT token handling utilities"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    """Token payload data"""

    user_id: UUID
    email: str
    exp: datetime


def create_access_token(user_id: UUID, email: str) -> tuple[str, int]:
    """
    Create a JWT access token.

    Args:
        user_id: User ID
        email: User email

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_in_minutes * 60


def create_refresh_token(user_id: UUID, email: str) -> tuple[str, int]:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID
        email: User email

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expire = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_in_days * 24 * 60 * 60


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != token_type:
            return None

        user_id_raw = payload.get("user_id")
        email_raw = payload.get("email")
        exp_raw = payload.get("exp")

        if user_id_raw is None or email_raw is None or exp_raw is None:
            return None

        if not isinstance(exp_raw, (int, float)):
            return None

        try:
            user_id = UUID(str(user_id_raw))
            exp = datetime.fromtimestamp(exp_raw, tz=timezone.utc)
        except (TypeError, ValueError):
            return None

        return TokenData(user_id=user_id, email=str(email_raw), exp=exp)

    except JWTError:
        return None
