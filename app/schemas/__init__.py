"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import Optional
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


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

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


class SimpleErrorResponse(BaseModel):
    """Simple error response schema matching FastAPI HTTPException"""

    detail: str
