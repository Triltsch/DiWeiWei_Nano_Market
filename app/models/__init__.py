"""SQLAlchemy models for the application"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    pass


class UserStatus(str, enum.Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, enum.Enum):
    """User roles in the system"""

    ADMIN = "admin"
    CREATOR = "creator"
    CONSUMER = "consumer"
    MODERATOR = "moderator"


class User(Base):
    """User entity"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Personal information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Encrypted in real app
    profile_avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # S3 URL

    # Account metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status and role
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.CONSUMER, nullable=False
    )

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(5), default="de", nullable=False)

    # Account security
    login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # GDPR/DSGVO Compliance
    accepted_terms: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when user accepted Terms of Service",
    )
    accepted_privacy: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when user accepted Privacy Policy",
    )
    deletion_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when user requested account deletion",
    )
    deletion_scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when account will be permanently deleted",
    )
    deletion_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional user-provided reason for account deletion",
    )

    def __repr__(self) -> str:
        """String representation of the user"""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class ConsentType(str, enum.Enum):
    """Types of consent that can be tracked"""

    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MARKETING = "marketing"
    DATA_PROCESSING = "data_processing"


class ConsentAudit(Base):
    """Audit log for user consent tracking (GDPR compliance)"""

    __tablename__ = "consent_audit"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who gave or revoked consent",
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        SQLEnum(ConsentType), nullable=False, index=True, comment="Type of consent"
    )
    accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="True if consent was given, False if revoked"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP address from which consent was given (IPv4 or IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Browser user agent string"
    )

    def __repr__(self) -> str:
        """String representation of consent audit entry"""
        return f"<ConsentAudit(user_id={self.user_id}, type={self.consent_type}, accepted={self.accepted})>"
