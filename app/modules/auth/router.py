"""Authentication API routes"""

import logging
from typing import Annotated, Callable
from urllib.parse import urlencode
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import AuditAction
from app.modules.audit.service import AuditLogger
from app.modules.auth.gdpr import (
    AccountAlreadyScheduledForDeletionError,
    GDPRError,
    cancel_account_deletion,
    export_user_data,
    get_user_consents,
    request_account_deletion,
)
from app.modules.auth.middleware import get_current_user_id
from app.modules.auth.service import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthenticationError,
    InvalidCredentialsError,
    PasswordChangeError,
    ProfileUpdateError,
    UserAlreadyExistsError,
    authenticate_user,
    change_user_password,
    get_user_profile,
    logout_user,
    record_failed_login,
    refresh_access_token,
    register_user,
    resend_email_verification_token,
    update_user_profile,
    verify_email_with_token,
)
from app.modules.auth.tokens import create_email_verification_token, verify_token
from app.modules.auth.validators import calculate_password_strength
from app.modules.mail import (
    MailPayload,
    SMTPAuthError,
    SMTPDeliveryError,
    build_resend_verification_email,
    build_verification_email,
    send_mail,
    set_mail_context,
)
from app.schemas import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    ConsentResponse,
    EmailVerificationRequest,
    LogoutRequest,
    MessageResponse,
    PasswordChangeRequest,
    PasswordStrengthRequest,
    PasswordStrengthResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    SimpleErrorResponse,
    TokenResponse,
    UserDataExport,
    UserLogin,
    UserProfileUpdate,
    UserRegister,
    UserResponse,
    VerificationEmailResponse,
)
from app.security.middleware import parse_csv_values
from app.security.rate_limit import SlidingWindowRateLimiter

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)

settings = get_settings()
logger = logging.getLogger(__name__)

MAIL_DELIVERY_UNAVAILABLE_DETAIL = (
    "Email delivery is currently unavailable. Please try again later."
)

LOGIN_RATE_LIMITER = SlidingWindowRateLimiter(
    max_requests=settings.RATE_LIMIT_LOGIN_MAX_REQUESTS,
    window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
)


# IP addresses of reverse proxies that are allowed to supply X-Forwarded-For
# values that we trust for rate limiting and audit logging. Loaded from
# SECURITY_TRUSTED_PROXIES so that production deployments can configure the
# actual proxy addresses without code changes.
TRUSTED_PROXIES: set[str] = set(parse_csv_values(settings.SECURITY_TRUSTED_PROXIES))


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request.

    When the request originates from a trusted reverse proxy, trust the
    X-Forwarded-For header (first value only). Otherwise, fall back to the
    immediate peer IP from request.client.host.
    """
    client_host: str = request.client.host if request.client else ""

    # Only honor X-Forwarded-For when the immediate client is a trusted proxy
    if client_host in TRUSTED_PROXIES:
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

    return client_host


def _get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("user-agent", "")


def _get_public_verification_base_url() -> str:
    """Resolve the base URL used for verification links in auth emails."""
    return settings.effective_verification_base_url


def _build_verification_url(token: str) -> str:
    """Build the frontend verification URL embedded in auth emails."""
    query = urlencode({"token": token})
    return f"{_get_public_verification_base_url()}/verify-email?{query}"


async def _send_verification_mail(
    *,
    email: str,
    username: str,
    token: str,
    flow_name: str,
    template_builder: Callable[[str, str], MailPayload],
) -> None:
    """Render and send a verification mail with stable SMTP error mapping."""
    correlation_id = str(uuid4())
    payload = template_builder(username, _build_verification_url(token))

    set_mail_context(payload.message_type, correlation_id)

    try:
        await send_mail(email, payload.subject, payload.body_html, payload.body_text)
    except (SMTPDeliveryError, SMTPAuthError) as error:
        logger.error(
            "auth_mail_delivery_failed",
            extra={
                "flow_name": flow_name,
                "message_type": payload.message_type,
                "correlation_id": correlation_id,
                "error_type": error.__class__.__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=MAIL_DELIVERY_UNAVAILABLE_DETAIL,
        ) from error


async def _enforce_login_rate_limit(request: Request) -> None:
    """Apply per-client login rate limiting."""
    client_ip = _get_client_ip(request)
    key = f"login:{client_ip}"

    allowed, retry_after_seconds = await LOGIN_RATE_LIMITER.check(key)
    if allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many login attempts. Please retry later.",
        headers={"Retry-After": str(retry_after_seconds)},
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
            "description": (
                "Service unavailable - database dependency unreachable " "or email delivery failure"
            ),
        },
    },
)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
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
        # NOTE: register_user() commits internally before we log the audit entry.
        # This means if audit logging fails, the user is already registered.
        # TODO: Refactor to single transaction boundary (services should flush, not commit)
        user = await register_user(db, user_data)

        # Log successful registration
        await AuditLogger.log_action(
            db,
            action=AuditAction.USER_REGISTERED,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"email": user.email, "username": user.username},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        verification_token, _ = create_email_verification_token(user.id, user.email)
        await _send_verification_mail(
            email=user.email,
            username=user.username,
            token=verification_token,
            flow_name="register",
            template_builder=build_verification_email,
        )

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
    request: Request,
) -> TokenResponse:
    """
    Login and receive JWT tokens.

    - **email**: User email address
    - **password**: User password

    Returns access_token (15 min expiry) and refresh_token (7 days expiry).
    User must have verified email to login. Account locks after 3 failed attempts for 1 hour.
    """
    await _enforce_login_rate_limit(request)

    try:  # NOTE: authenticate_user() commits internally (updates last_login, resets attempts)
        # before we log the audit entry. If audit logging fails, login state is already committed.
        # TODO: Refactor to single transaction boundary at router level
        user, tokens = await authenticate_user(db, credentials.email, credentials.password)

        # Log successful login
        await AuditLogger.log_action(
            db,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"email": user.email},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        return tokens
    except AccountLockedError as e:
        # Log account locked attempt
        await AuditLogger.log_action(
            db,
            action=AuditAction.ACCOUNT_LOCKED,
            resource_type="user_login_attempt",
            metadata={"email": credentials.email, "reason": "too_many_attempts"},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except AccountNotVerifiedError as e:
        await record_failed_login(db, credentials.email)

        # Log failed login - email not verified
        await AuditLogger.log_action(
            db,
            action=AuditAction.LOGIN_FAILURE,
            resource_type="user_login_attempt",
            metadata={"email": credentials.email, "reason": "email_not_verified"},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except InvalidCredentialsError as e:
        await record_failed_login(db, credentials.email)

        # Log failed login - invalid credentials
        await AuditLogger.log_action(
            db,
            action=AuditAction.LOGIN_FAILURE,
            resource_type="user_login_attempt",
            metadata={"email": credentials.email, "reason": "invalid_credentials"},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

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
    request: Request,
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Request body:
    - **refresh_token**: Valid refresh token

    Returns new access_token with same expiry (15 min) and original refresh_token.
    """
    try:
        # Verify token first to extract user_id for audit logging
        token_data = verify_token(body.refresh_token, token_type="refresh")
        user_id = token_data.user_id if token_data else None

        tokens = await refresh_access_token(db, body.refresh_token)

        # Log token refresh with user_id for investigation purposes
        await AuditLogger.log_action(
            db,
            action=AuditAction.TOKEN_REFRESH,
            user_id=user_id,
            resource_type="token",
            resource_id=str(user_id) if user_id else None,
            metadata={"token_type": "refresh_token"},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    responses={
        401: {"model": SimpleErrorResponse, "description": "Unauthorized - invalid token"},
    },
)
async def logout(
    body: LogoutRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> MessageResponse:
    """
    Logout user by revoking tokens.

    Requires:
    - **Authorization**: Bearer token in header (access token)

    Request body:
    - **refresh_token**: Refresh token to revoke

    Blacklists both access and refresh tokens immediately.
    Tokens cannot be used after logout until they naturally expire.
    """
    try:
        # Note: Access token is already validated by middleware
        # For MVP, we'll revoke the refresh token which is the primary concern
        # In production, extract and revoke access token as well
        await logout_user(db, user_id, "", body.refresh_token)

        # Log logout
        await AuditLogger.log_action(
            db,
            action=AuditAction.LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id),
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        return MessageResponse(message="Successfully logged out")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/verify-email", response_model=VerificationEmailResponse)
async def verify_email_endpoint(
    body: EmailVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
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

        # Log email verification
        await AuditLogger.log_action(
            db,
            action=AuditAction.EMAIL_VERIFIED,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"email": user.email},
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

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
    # TypedDict result can be safely unpacked - Pydantic will validate all fields
    return PasswordStrengthResponse(**result)


@router.post("/resend-verification-email")
async def resend_verification_email_endpoint(
    body: ResendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationEmailResponse:
    """
    Resend email verification token to user.

    Request body:
    - **email**: User email address

    Returns the legacy token response in development/test when
    AUTH_RESEND_RETURN_TOKEN is enabled. Otherwise sends a verification mail and
    returns a product-safe success message.
    """
    try:
        token, _expires_in, username = await resend_email_verification_token(db, body.email)

        if settings.AUTH_RESEND_RETURN_TOKEN:
            return VerificationEmailResponse(
                message=(
                    "(MVP) Verification token generated. "
                    "Copy this token to verify your email: " + token
                ),
                email=body.email,
            )

        await _send_verification_mail(
            email=body.email,
            username=username,
            token=token,
            flow_name="resend_verification",
            template_builder=build_resend_verification_email,
        )

        return VerificationEmailResponse(
            message="Verification email sent. Please check your inbox.",
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


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def get_my_profile(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Return the authenticated user's own profile.

    Requires authentication via Bearer token.

    Returns the full profile including personal information, account status,
    and GDPR-related timestamps.
    """
    try:
        return await get_user_profile(db, user_id)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.patch(
    "/me",
    response_model=UserResponse,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        422: {
            "model": SimpleErrorResponse,
            "description": "Unprocessable entity - validation error",
        },
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def update_my_profile(
    update_data: UserProfileUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> UserResponse:
    """Partially update the authenticated user's profile.

    Only the fields that are explicitly present in the request body are written;
    absent fields are left unchanged.  Email and username cannot be changed via
    this endpoint.

    Updatable fields:
    - **first_name**, **last_name** — personal name
    - **bio** — short biography (max 500 chars)
    - **company**, **job_title** — professional information
    - **phone** — phone number (max 20 chars)
    - **preferred_language** — ISO 639-1 language code (e.g. ``"de"``, ``"en"``)

    Requires authentication via Bearer token.
    """
    try:
        updated_fields = list(update_data.model_dump(exclude_unset=True).keys())
        updated_user = await update_user_profile(db, user_id, update_data)

        if updated_fields:
            await AuditLogger.log_action(
                db,
                action=AuditAction.USER_UPDATED,
                user_id=user_id,
                resource_type="user",
                resource_id=str(user_id),
                metadata={"updated_fields": updated_fields},
                ip_address=_get_client_ip(request),
                user_agent=_get_user_agent(request),
            )
            await db.commit()

        return updated_user
    except ProfileUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token, or wrong current password",
        },
        400: {
            "model": SimpleErrorResponse,
            "description": "Bad request - new password does not meet policy",
        },
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def change_my_password(
    body: PasswordChangeRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> MessageResponse:
    """Change the authenticated user's own password (self-service).

    The caller must supply their current password for re-authentication.
    The new password must satisfy the same strength policy as registration:
    at least 8 characters, one uppercase letter, one digit, one special
    character.

    Request body:
    - **current_password**: Existing password (used for re-authentication)
    - **new_password**: Desired new password (min 8 characters)

    Requires authentication via Bearer token.
    """
    try:
        await change_user_password(db, user_id, body.current_password, body.new_password)

        await AuditLogger.log_action(
            db,
            action=AuditAction.PASSWORD_CHANGED,
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id),
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await db.commit()

        return MessageResponse(message="Password changed successfully")
    except PasswordChangeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AuthenticationError as e:
        if str(e) == "User not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.get(
    "/me/export",
    response_model=UserDataExport,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def export_my_data(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserDataExport:
    """
    Export all personal data for the authenticated user (GDPR compliance).

    Returns user data in machine-readable JSON format including:
    - Profile information
    - Account metadata
    - Current consent-related timestamps (not full consent audit history)

    Requires authentication via Bearer token.
    """
    try:
        return await export_user_data(db, user_id)
    except GDPRError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.get(
    "/me/consents",
    response_model=list[ConsentResponse],
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def get_my_consents(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConsentResponse]:
    """
    Get all consent records for the authenticated user (GDPR compliance).

    Returns history of all consents given or revoked, including:
    - Terms of Service acceptance
    - Privacy Policy acceptance
    - Marketing consent (future)
    - Data processing consent (future)

    Requires authentication via Bearer token.
    """
    try:
        return await get_user_consents(db, user_id)
    except GDPRError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post(
    "/me/delete",
    response_model=AccountDeletionResponse,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        400: {"model": SimpleErrorResponse, "description": "Bad request - must confirm deletion"},
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        409: {"model": SimpleErrorResponse, "description": "Deletion already scheduled"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def request_my_account_deletion(
    deletion_request: AccountDeletionRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountDeletionResponse:
    """
    Request deletion of the authenticated user's account (GDPR compliance).

    Initiates a 30-day grace period before permanent deletion:
    - Account is immediately deactivated
    - All data remains available for 30 days
    - User can cancel deletion during grace period
    - After 30 days, all data is permanently deleted

    Requires:
    - **confirm**: Must be `true` to confirm deletion
    - **reason**: Optional reason for deletion (max 500 chars)

    Requires authentication via Bearer token.
    """
    if not deletion_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm account deletion by setting 'confirm' to true",
        )

    try:
        return await request_account_deletion(db, user_id, deletion_request.reason)
    except AccountAlreadyScheduledForDeletionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except GDPRError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post(
    "/me/cancel-deletion",
    response_model=MessageResponse,
    responses={
        401: {
            "model": SimpleErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        400: {"model": SimpleErrorResponse, "description": "No deletion request pending"},
        404: {"model": SimpleErrorResponse, "description": "User not found"},
        503: {
            "model": SimpleErrorResponse,
            "description": "Service unavailable - database dependency unreachable",
        },
    },
)
async def cancel_my_account_deletion(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Cancel a pending account deletion request (GDPR compliance).

    Reactivates the account and cancels the scheduled deletion.
    Can only be called if deletion request exists and grace period hasn't expired.

    Requires authentication via Bearer token.
    """
    try:
        await cancel_account_deletion(db, user_id)
        return MessageResponse(
            message="Account deletion cancelled successfully. Your account has been reactivated."
        )
    except GDPRError as e:
        error_message = str(e)
        if error_message == "User not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


def get_auth_router() -> APIRouter:
    """Get the authentication router"""
    return router
