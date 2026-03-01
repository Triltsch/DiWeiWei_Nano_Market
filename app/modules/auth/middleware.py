"""Authentication middleware for JWT token validation"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.tokens import TokenData, verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """
    Validate JWT access token and return token data.

    This dependency can be used to protect endpoints requiring authentication.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is invalid, expired, or blacklisted
    """
    token = credentials.credentials

    # Verify token
    token_data = verify_token(token, token_type="access")

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def get_current_user_id(
    token_data: Annotated[TokenData, Depends(get_current_user)],
) -> UUID:
    """
    Extract user ID from validated token.

    Args:
        token_data: Validated token data

    Returns:
        User ID
    """
    return token_data.user_id
