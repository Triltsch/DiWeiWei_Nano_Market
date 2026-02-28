"""Authentication middleware for JWT token validation"""

from collections.abc import Awaitable, Callable
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.tokens import TokenData, verify_token
from app.redis_client import is_token_blacklisted

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

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[TokenData]:
    """
    Validate JWT access token if provided, return None if not provided.

    This dependency can be used for endpoints that optionally require authentication.

    Args:
        credentials: Optional HTTP Bearer token from Authorization header

    Returns:
        TokenData if token provided and valid, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        return None

    # Verify token
    token_data = verify_token(token, token_type="access")

    return token_data


def require_role(
    required_role: str,
) -> Callable[[Annotated[TokenData, Depends(get_current_user)]], Awaitable[TokenData]]:
    """
    Dependency factory to require specific user role.

    Args:
        required_role: Required role ("consumer", "creator", "admin", "moderator")

    Returns:
        Dependency function that checks user role

    Example:
        @router.get("/admin/users", dependencies=[Depends(require_role("admin"))])
        async def list_users():
            ...
    """

    async def check_role(token_data: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if token_data.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {required_role} role",
            )
        return token_data

    return check_role
