"""SQLAlchemy models for the application"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
        SQLEnum(UserRole), default=UserRole.CREATOR, nullable=False
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


class AuditAction(str, enum.Enum):
    """Audit log action types"""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_BLACKLIST = "token_blacklist"

    # User management events
    USER_REGISTERED = "user_registered"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    EMAIL_VERIFIED = "email_verified"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"

    # Admin actions
    USER_SUSPENDED = "user_suspended"
    USER_UNSUSPENDED = "user_unsuspended"
    ROLE_CHANGED = "role_changed"
    USER_DELETED_BY_ADMIN = "user_deleted_by_admin"

    # Security events
    FAILED_SECURITY_CHECK = "failed_security_check"
    RATE_LIMIT_HIT = "rate_limit_hit"
    INVALID_TOKEN = "invalid_token"
    PERMISSION_DENIED = "permission_denied"

    # Data events
    DATA_CREATED = "data_created"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_ACCESSED = "data_accessed"

    # Consent events
    CONSENT_GIVEN = "consent_given"
    CONSENT_REVOKED = "consent_revoked"
    DELETION_REQUESTED = "deletion_requested"
    DELETION_CONFIRMED = "deletion_confirmed"

    # Moderation events (Story 6.2 — Content Review Workflow)
    MODERATION_APPROVED = "moderation_approved"
    MODERATION_REJECTED = "moderation_rejected"
    MODERATION_DEFERRED = "moderation_deferred"
    MODERATION_ESCALATED = "moderation_escalated"
    FLAG_CREATED = "flag_created"
    FLAG_REVIEWED = "flag_reviewed"


class FeedbackModerationStatus(str, enum.Enum):
    """Moderation lifecycle for ratings and comments."""

    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


class AuditLog(Base):
    """Audit log for tracking user actions and system events"""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (NULL for system events)",
    )
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction), nullable=False, index=True, comment="Type of action performed"
    )
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of resource affected (user, data, etc.)",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, index=True, comment="ID of the resource affected"
    )
    event_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        comment="Additional context about the action",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address from which action originated (IPv4 or IPv6)",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Browser user agent string"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp when action occurred",
    )

    def __repr__(self) -> str:
        """String representation of audit log entry"""
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, resource_type={self.resource_type})>"


# ================================
# Nano Domain Models (Sprint 2)
# ================================


class NanoStatus(str, enum.Enum):
    """Status of a Nano in the publishing workflow"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NanoFormat(str, enum.Enum):
    """Format/type of the Nano content"""

    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    MIXED = "mixed"


class CompetencyLevel(int, enum.Enum):
    """Didactic/competency level (1=Basic, 2=Intermediate, 3=Advanced)"""

    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class LicenseType(str, enum.Enum):
    """Content license types"""

    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    CC0 = "CC0"
    PROPRIETARY = "proprietary"


class Nano(Base):
    """
    Nano entity - Core learning unit model.

    Represents uploadable learning content with metadata,
    versioning, and publishing workflow support.
    """

    __tablename__ = "nanos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # Ownership
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Creator/owner of the Nano",
    )

    # Core metadata
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Nano title (max 200 chars)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Detailed description (max 1000 chars)"
    )

    # Learning metadata
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Estimated duration in minutes"
    )
    competency_level: Mapped[CompetencyLevel] = mapped_column(
        SQLEnum(CompetencyLevel),
        default=CompetencyLevel.BASIC,
        nullable=False,
        index=True,
        comment="Didactic level (1=Basic, 2=Intermediate, 3=Advanced)",
    )
    language: Mapped[str] = mapped_column(
        String(5), default="de", nullable=False, index=True, comment="Content language (ISO 639-1)"
    )
    format: Mapped[NanoFormat] = mapped_column(
        SQLEnum(NanoFormat),
        default=NanoFormat.MIXED,
        nullable=False,
        comment="Content format/type",
    )

    # Publishing workflow
    status: Mapped[NanoStatus] = mapped_column(
        SQLEnum(NanoStatus),
        default=NanoStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Publishing status",
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", nullable=False, comment="Semantic version (semver)"
    )

    # Storage references
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Thumbnail image URL (object storage)"
    )
    file_storage_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="ZIP file path in object storage (MinIO)"
    )

    # License
    license: Mapped[LicenseType] = mapped_column(
        SQLEnum(LicenseType),
        default=LicenseType.PROPRIETARY,
        nullable=False,
        comment="Content license",
    )

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True, comment="When Nano was published"
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When Nano was archived"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Denormalized cache fields for performance
    download_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total downloads (cache)"
    )
    average_rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
        nullable=False,
        index=True,
        comment="Average rating 0.00-5.00 (cache)",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total ratings (cache)"
    )

    def __repr__(self) -> str:
        """String representation of Nano"""
        return f"<Nano(id={self.id}, title={self.title}, status={self.status})>"


class ChatSession(Base):
    """Direct chat session between a Nano creator and one participant."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        UniqueConstraint(
            "nano_id",
            "creator_id",
            "participant_user_id",
            name="uq_chat_sessions_nano_creator_participant",
        ),
        CheckConstraint(
            "creator_id <> participant_user_id",
            name="ck_chat_sessions_distinct_participants",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Referenced Nano for the chat context",
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Nano creator participating in this chat",
    )
    participant_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Non-creator participant in this chat",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp of last message in this session",
    )

    def __repr__(self) -> str:
        """String representation of ChatSession."""
        return (
            f"<ChatSession(id={self.id}, nano_id={self.nano_id}, "
            f"creator_id={self.creator_id}, participant_user_id={self.participant_user_id})>"
        )


class ChatMessage(Base):
    """A single message in a direct chat session.

    Supports polling-based retrieval via the ``created_at`` index.
    Content is validated at both the Pydantic and DB constraint level (1–1000 characters).
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(
            "length(content) >= 1",
            name="ck_chat_messages_content_non_empty",
        ),
        CheckConstraint(
            "length(content) <= 1000",
            name="ck_chat_messages_content_max_length",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chat session this message belongs to",
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who sent the message",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content (1–1000 characters)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the message was sent; used as polling cursor",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of ChatMessage."""
        return (
            f"<ChatMessage(id={self.id}, session_id={self.session_id}, "
            f"sender_id={self.sender_id})>"
        )


class NanoRating(Base):
    """User star rating for a published Nano."""

    __tablename__ = "nano_ratings"
    __table_args__ = (
        UniqueConstraint("nano_id", "user_id", name="uq_nano_ratings_nano_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_nano_ratings_score_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Rated Nano",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who submitted the rating",
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Star score between 1 and 5",
    )
    moderation_status: Mapped[FeedbackModerationStatus] = mapped_column(
        SQLEnum(FeedbackModerationStatus),
        default=FeedbackModerationStatus.PENDING,
        nullable=False,
        index=True,
        comment="Moderation status for rating visibility",
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of latest moderation decision",
    )
    moderated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Moderator/admin who made the latest decision",
    )
    moderation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional reason for the latest moderation decision",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of NanoRating."""
        return f"<NanoRating(id={self.id}, nano_id={self.nano_id}, user_id={self.user_id}, score={self.score})>"


class NanoComment(Base):
    """User comment/review for a published Nano."""

    __tablename__ = "nano_comments"
    __table_args__ = (
        UniqueConstraint("nano_id", "user_id", name="uq_nano_comments_nano_user"),
        CheckConstraint("length(content) >= 1", name="ck_nano_comments_content_non_empty"),
        CheckConstraint("length(content) <= 1000", name="ck_nano_comments_content_max_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reviewed Nano",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who submitted the comment",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Sanitized comment content (1-1000 chars)",
    )
    moderation_status: Mapped[FeedbackModerationStatus] = mapped_column(
        SQLEnum(FeedbackModerationStatus),
        default=FeedbackModerationStatus.PENDING,
        nullable=False,
        index=True,
        comment="Moderation status for comment visibility",
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of latest moderation decision",
    )
    moderated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Moderator/admin who made the latest decision",
    )
    moderation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional reason for the latest moderation decision",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        """String representation of NanoComment."""
        return f"<NanoComment(id={self.id}, nano_id={self.nano_id}, " f"user_id={self.user_id})>"


class NanoVersion(Base):
    """
    Nano version audit trail.

    Immutable ledger of Nano version history for audit/rollback purposes.
    """

    __tablename__ = "nano_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent Nano",
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Semantic version (semver)"
    )
    changelog: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="What changed in this version"
    )
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who created this version",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    file_storage_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Snapshot of file path at this version"
    )
    status: Mapped[NanoStatus] = mapped_column(
        SQLEnum(NanoStatus),
        default=NanoStatus.PUBLISHED,
        nullable=False,
        comment="Version status",
    )

    def __repr__(self) -> str:
        """String representation of NanoVersion"""
        return f"<NanoVersion(id={self.id}, nano_id={self.nano_id}, version={self.version})>"


class Category(Base):
    """
    Category/Tag dictionary for Nano classification.

    Hierarchical category system for content organization.
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="Category name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Category description"
    )
    parent_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent category for hierarchy",
    )
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Category icon URL"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, comment="active or inactive"
    )

    def __repr__(self) -> str:
        """String representation of Category"""
        return f"<Category(id={self.id}, name={self.name})>"


class NanoCategoryAssignment(Base):
    """
    Many-to-many relationship between Nanos and Categories.

    Allows Nanos to be tagged with multiple categories (max 5).
    """

    __tablename__ = "nano_category_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Nano reference",
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Category reference",
    )
    rank: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Display order/priority"
    )

    def __repr__(self) -> str:
        """String representation of NanoCategoryAssignment"""
        return f"<NanoCategoryAssignment(nano_id={self.nano_id}, category_id={self.category_id})>"


# ================================
# Moderation Domain Models (Sprint 8 — Story 6.2)
# ================================


class ModerationCaseStatus(str, enum.Enum):
    """Lifecycle status of a moderation review case.

    PENDING   - awaiting a moderator decision
    APPROVED  - content was approved (made visible / published)
    REJECTED  - content was rejected (hidden / reverted to draft)
    DEFERRED  - decision postponed until a later date
    ESCALATED - routed to a senior moderator or admin for further review
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    ESCALATED = "escalated"


class ModerationContentType(str, enum.Enum):
    """Type of content tracked by a moderation case.

    NANO         - a learning-content Nano in pending_review status
    NANO_RATING  - a user star-rating awaiting feedback moderation
    NANO_COMMENT - a user comment awaiting feedback moderation
    FLAG         - reserved for Story 6.3 (user-reported flags); not yet in use
    """

    NANO = "nano"
    NANO_RATING = "nano_rating"
    NANO_COMMENT = "nano_comment"
    FLAG = "flag"  # reserved: Story 6.3


class FlagReason(str, enum.Enum):
    """Reason selected by a user when reporting a Nano."""

    SPAM = "spam"
    COPYRIGHT = "copyright"
    OFFENSIVE = "offensive"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class FlagStatus(str, enum.Enum):
    """Lifecycle status of a user-submitted Nano flag."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NanoFlag(Base):
    """User-submitted flag for inappropriate or policy-violating Nano content."""

    __tablename__ = "nano_flags"
    __table_args__ = (
        UniqueConstraint("nano_id", "flagging_user_id", name="uq_nano_flags_nano_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nanos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Flagged Nano",
    )
    flagging_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who submitted this flag",
    )
    reason: Mapped[FlagReason] = mapped_column(
        SQLEnum(FlagReason),
        nullable=False,
        comment="Selected report reason",
    )
    comment: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional user comment (max 500 chars)",
    )
    status: Mapped[FlagStatus] = mapped_column(
        SQLEnum(FlagStatus),
        default=FlagStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status of the flag workflow",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the flag was submitted",
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When a moderator/admin reviewed this flag",
    )
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Moderator/admin who reviewed this flag",
    )

    def __repr__(self) -> str:
        """String representation of NanoFlag."""
        return (
            f"<NanoFlag(id={self.id}, nano_id={self.nano_id}, "
            f"flagging_user_id={self.flagging_user_id}, status={self.status})>"
        )


class ModerationCase(Base):
    """Moderation review case for auditable content decisions.

    One case exists per reviewable content item (Nano, rating, or comment).
    When content re-enters review (e.g., an updated rating) the existing case
    is reset to PENDING so its full decision history is preserved via the
    audit_logs table while the case reflects the current active state.

    The ``reporter_id`` column is intentionally nullable and reserved for
    Story 6.3, where user-submitted flags will populate it. All flag-driven
    cases will share the same decision flow as internally generated cases.
    """

    __tablename__ = "moderation_cases"
    __table_args__ = (
        UniqueConstraint(
            "content_type",
            "content_id",
            name="uq_moderation_cases_content",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # Content reference - polymorphic pointer to the reviewed item
    content_type: Mapped[ModerationContentType] = mapped_column(
        SQLEnum(ModerationContentType),
        nullable=False,
        index=True,
        comment="Type of content being reviewed (nano, nano_rating, nano_comment, flag)",
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Primary key of the reviewed content record",
    )

    # Optional reporter - NULL for admin/system-initiated cases; populated by Story 6.3 flags
    reporter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who reported the content (NULL for internally generated cases)",
    )

    # Decision state
    status: Mapped[ModerationCaseStatus] = mapped_column(
        SQLEnum(ModerationCaseStatus),
        default=ModerationCaseStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current review status of this case",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Moderator-provided reason for the decision (max 500 chars)",
    )
    decided_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Moderator/admin who made the most recent decision",
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the most recent decision",
    )

    # Defer / escalate metadata
    deferred_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Re-review date for DEFERRED cases",
    )
    escalation_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason provided when escalating to a senior moderator",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When this case was opened",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When this case was last modified",
    )

    def __repr__(self) -> str:
        """String representation of ModerationCase."""
        return (
            f"<ModerationCase(id={self.id}, content_type={self.content_type}, "
            f"content_id={self.content_id}, status={self.status})>"
        )
