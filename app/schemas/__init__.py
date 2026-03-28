"""Pydantic schemas for request/response validation"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    preferred_language: str = Field(default="de", max_length=5)


class UserRegister(UserBase):
    """User registration request schema"""

    password: str = Field(..., min_length=8)
    accept_terms: bool = Field(..., description="User must accept Terms of Service")
    accept_privacy: bool = Field(..., description="User must accept Privacy Policy")


class UserLogin(BaseModel):
    """User login request schema"""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: UserStatus
    role: UserRole
    email_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    profile_avatar: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    accepted_terms: Optional[datetime] = None
    accepted_privacy: Optional[datetime] = None
    deletion_requested_at: Optional[datetime] = None
    deletion_scheduled_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema"""

    refresh_token: str


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""

    token: str = Field(..., description="Email verification token")


class MessageResponse(BaseModel):
    """Generic message response schema"""

    message: str


class VerificationEmailResponse(BaseModel):
    """Email verification response schema"""

    message: str
    email: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema"""

    email: EmailStr


class ErrorResponse(BaseModel):
    """Error response schema"""

    detail: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.now)


class UserDataExport(BaseModel):
    """User data export schema for GDPR compliance"""

    export_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool
    verified_at: Optional[datetime] = None
    status: str
    role: str
    accepted_terms: Optional[datetime] = None
    accepted_privacy: Optional[datetime] = None


class AccountDeletionRequest(BaseModel):
    """Account deletion request schema"""

    confirm: bool = Field(..., description="Must be true to confirm deletion")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for deletion")


class AccountDeletionResponse(BaseModel):
    """Account deletion response schema"""

    message: str
    deletion_scheduled_at: datetime
    grace_period_days: int = 30


class ConsentResponse(BaseModel):
    """Consent information response schema"""

    consent_type: str
    accepted: bool
    timestamp: datetime


class SimpleErrorResponse(BaseModel):
    """Simple error response schema matching FastAPI HTTPException"""

    detail: str


class PasswordStrengthRequest(BaseModel):
    """Password strength check request schema"""

    password: str = Field(..., description="Password to evaluate")


class PasswordStrengthResponse(BaseModel):
    """
    Password strength evaluation response.

    Provides a strength score (0-100) and actionable suggestions for improvement.
    """

    score: int = Field(
        ..., ge=0, le=100, description="Strength score from 0 (weakest) to 100 (strongest)"
    )
    strength: str = Field(
        ...,
        description="Strength label: weak, fair, good, strong, or very_strong",
    )
    suggestions: list[str] = Field(
        ...,
        description="List of suggestions to improve password strength",
    )
    meets_policy: bool = Field(
        ...,
        description="Whether password meets minimum security policy requirements",
    )


class AuditLogResponse(BaseModel):
    """Audit log response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AuditLogsQueryResponse(BaseModel):
    """Paginated audit logs query response schema"""

    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class SuspiciousActivityResponse(BaseModel):
    """Suspicious activity detection response schema"""

    user_id: UUID
    activity_count: int
    logs: list[AuditLogResponse]
    message: str


class UserProfileUpdate(BaseModel):
    """Schema for partial user profile update (PATCH /me).

    All fields are optional—only provided fields are applied.
    Email and username are not updatable via this endpoint; they require
    dedicated verification flows.
    """

    first_name: Optional[str] = Field(None, max_length=100, description="Given name")
    last_name: Optional[str] = Field(None, max_length=100, description="Family name")
    bio: Optional[str] = Field(None, max_length=500, description="Short biography (max 500 chars)")
    company: Optional[str] = Field(None, max_length=255, description="Company or organisation")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title or role")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    preferred_language: Optional[str] = Field(
        None, max_length=5, description="ISO 639-1 language code (e.g. 'de', 'en')"
    )


class PasswordChangeRequest(BaseModel):
    """Schema for the authenticated password-change self-service flow (POST /me/change-password).

    The caller must supply their current password for re-authentication before the
    new password is accepted.  The new password must satisfy the same strength policy
    as registration.
    """

    current_password: str = Field(..., description="Current account password for re-authentication")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
