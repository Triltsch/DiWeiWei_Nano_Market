"""JWT token handling utilities"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    """Token payload data"""

    user_id: UUID
    email: str
    role: str
    exp: datetime
    iat: datetime


def create_access_token(user_id: UUID, email: str, role: str = "consumer") -> tuple[str, int]:
    """
    Create a JWT access token with standard claims.

    Args:
        user_id: User ID
        email: User email
        role: User role (default: "consumer")

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_in_minutes)

    payload = {
        "sub": str(user_id),  # Standard JWT "subject" claim
        "user_id": str(user_id),  # Keep for backward compatibility
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),  # Standard JWT "issued at" claim
        "exp": expire,
        "jti": str(uuid4()),  # Ensure token uniqueness for same-second issuance
        "type": "access",
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_in_minutes * 60


def create_refresh_token(user_id: UUID, email: str, role: str = "consumer") -> tuple[str, int]:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID
        email: User email
        role: User role (default: "consumer")

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=expires_in_days)

    payload = {
        "sub": str(user_id),  # Standard JWT "subject" claim
        "user_id": str(user_id),  # Keep for backward compatibility
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),  # Standard JWT "issued at" claim
        "exp": expire,
        "jti": str(uuid4()),  # Ensure token uniqueness for rotation
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_in_days * 24 * 60 * 60


def create_email_verification_token(user_id: UUID, email: str) -> tuple[str, int]:
    """
    Create a JWT email verification token.

    Args:
        user_id: User ID
        email: User email

    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in_hours = settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire,
        "type": "email_verification",
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_in_hours * 60 * 60


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ('access', 'refresh', or 'email_verification')

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != token_type:
            return None

        # Extract claims using standard JWT field "sub" or fallback to "user_id"
        user_id_raw = payload.get("sub") or payload.get("user_id")
        email_raw = payload.get("email")
        role_raw = payload.get("role", "consumer")  # Default to consumer if not present
        exp_raw = payload.get("exp")
        iat_raw = payload.get("iat")

        if user_id_raw is None or email_raw is None or exp_raw is None:
            return None

        if not isinstance(exp_raw, (int, float)):
            return None

        try:
            user_id = UUID(str(user_id_raw))
            exp = datetime.fromtimestamp(exp_raw, tz=timezone.utc)

            # Handle iat - if present convert, otherwise use current time
            if iat_raw and isinstance(iat_raw, (int, float)):
                iat = datetime.fromtimestamp(iat_raw, tz=timezone.utc)
            else:
                iat = datetime.now(timezone.utc)

        except (TypeError, ValueError):
            return None

        return TokenData(
            user_id=user_id,
            email=str(email_raw),
            role=str(role_raw),
            exp=exp,
            iat=iat,
        )

    except JWTError:
        return None
