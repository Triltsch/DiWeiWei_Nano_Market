"""Authentication API routes"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError
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
    resend_email_verification_token,
    verify_email_with_token,
)
from app.modules.auth.validators import calculate_password_strength
from app.schemas import (
    EmailVerificationRequest,
    PasswordStrengthRequest,
    PasswordStrengthResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
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
        409: {
            "model": SimpleErrorResponse,
            "description": "Conflict - email or username already exists",
        },
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
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
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": SimpleErrorResponse, "description": "Unauthorized - invalid credentials"},
        403: {
            "model": SimpleErrorResponse,
            "description": "Forbidden - account locked or not verified",
        },
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
    body: EmailVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationEmailResponse:
    """
    Verify user email with verification token.

    Request body:
    - **token**: Email verification token (received via email)

    Returns verification confirmation with user email.

    The token expires after EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS (default: 24 hours).
    After verification, user can login successfully.
    """
    try:
        user = await verify_email_with_token(db, body.token)
        return VerificationEmailResponse(
            message="Email verified successfully. You can now login.",
            email=user.email,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post(
    "/check-password-strength",
    response_model=PasswordStrengthResponse,
    responses={
        200: {"description": "Password strength evaluation"},
    },
)
async def check_password_strength(
    body: PasswordStrengthRequest,
) -> PasswordStrengthResponse:
    """
    Evaluate password strength and provide improvement suggestions.

    Request body:
    - **password**: Password to evaluate (not stored or logged)

    Returns a strength evaluation including:
    - **score**: 0-100 strength score
    - **strength**: Label (weak, fair, good, strong, very_strong)
    - **suggestions**: List of actionable improvement tips
    - **meets_policy**: Whether password meets minimum security requirements

    Note: This endpoint does NOT store or log the password. It's designed
    for client-side feedback during registration or password changes.

    Scoring criteria:
    - Length (up to 40 points): 8+ chars recommended
    - Character variety (up to 40 points): lowercase, uppercase, digits, special chars
    - Complexity (up to 20 points): avoids common patterns and repetition
    """
    result = calculate_password_strength(body.password)
    return PasswordStrengthResponse(
        score=result["score"],
        strength=result["strength"],
        suggestions=result["suggestions"],
        meets_policy=result["meets_policy"],
    )


@router.post("/resend-verification-email")
async def resend_verification_email_endpoint(
    body: ResendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationEmailResponse:
    """
    Resend email verification token to user.

    Request body:
    - **email**: User email address

    Returns token information (token generation confirmed, but actual email sending
    not yet implemented). In production, the token would be sent via email.

    ## MVP Note
    Currently returns the token for manual testing. In production:
    - Token would be sent via email with verification link
    - Client would not receive token in response
    - Only confirmation message would be returned
    """
    try:
        token, expires_in = await resend_email_verification_token(db, body.email)
        return VerificationEmailResponse(
            message=(
                "(MVP) Verification token generated. "
                "Copy this token to verify your email: " + token
            ),
            email=body.email,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


def get_auth_router() -> APIRouter:
    """Get the authentication router"""
    return router
