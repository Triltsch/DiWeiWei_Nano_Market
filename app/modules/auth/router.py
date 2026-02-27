"""Authentication API routes"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.service import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    record_failed_login,
    refresh_access_token,
    register_user,
)
from app.schemas import (
    RefreshTokenRequest,
    SimpleErrorResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    VerificationEmailResponse,
)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": SimpleErrorResponse, "description": "Bad request - validation error"},
        409: {"model": SimpleErrorResponse, "description": "Conflict - email or username already exists"},
    },
)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Register a new user.

    - **email**: Valid email address (unique, case-insensitive)
    - **username**: 3-20 alphanumeric characters + underscore (unique)
    - **password**: Minimum 8 chars, 1 uppercase, 1 digit, 1 special character
    - **first_name**: Optional
    - **last_name**: Optional
    - **bio**: Optional, max 500 characters
    - **preferred_language**: ISO 639-1 language code (default: "de")

    Returns new user with ID and timestamps. Email verification required before login.
    """
    try:
        user = await register_user(db, user_data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": SimpleErrorResponse, "description": "Unauthorized - invalid credentials"},
        403: {"model": SimpleErrorResponse, "description": "Forbidden - account locked or not verified"},
    },
)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Login and receive JWT tokens.

    - **email**: User email address
    - **password**: User password

    Returns access_token (15 min expiry) and refresh_token (7 days expiry).
    User must have verified email to login. Account locks after 3 failed attempts for 1 hour.
    """
    try:
        user, tokens = await authenticate_user(db, credentials.email, credentials.password)
        return tokens
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except AccountNotVerifiedError as e:
        await record_failed_login(db, credentials.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except InvalidCredentialsError as e:
        await record_failed_login(db, credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    responses={
        401: {"model": SimpleErrorResponse, "description": "Unauthorized - invalid token"},
    },
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Request body:
    - **refresh_token**: Valid refresh token

    Returns new access_token with same expiry (15 min) and original refresh_token.
    """
    try:
        tokens = await refresh_access_token(db, body.refresh_token)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/verify-email", response_model=VerificationEmailResponse)
async def verify_email_endpoint(
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationEmailResponse:
    """
    Verify user email with verification token (placeholder).

    Request body:
    - **token**: Email verification token sent to user

    This endpoint is a placeholder for email verification.
    In production, token would be sent via email link.
    """
    # TODO: Implement email verification token verification
    # For now, this is a placeholder that would verify an email token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification not yet implemented",
    )


def get_auth_router() -> APIRouter:
    """Get the authentication router"""
    return router
