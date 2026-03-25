"""
Pydantic schemas for Nano metadata operations.

This module defines request and response models for the Nano metadata API endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MetadataUpdateRequest(BaseModel):
    """
    Request schema for updating Nano metadata.

    All fields are optional to support partial updates. At least one field
    must be provided in the request.

    Attributes:
        title: Nano title (1-200 chars)
        description: Detailed description (max 2000 chars)
        duration_minutes: Estimated duration in minutes (positive integer)
        competency_level: Learning level (beginner/intermediate/advanced)
        language: Content language (ISO 639-1, 2-5 chars)
        format: Content type (video/text/quiz/interactive/mixed)
        category_ids: List of category UUIDs to assign (max 5)
        license: Content license type
    """

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Nano title (1-200 characters)",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed description (max 2000 characters)",
    )
    duration_minutes: Optional[int] = Field(
        None,
        gt=0,
        le=1440,
        description="Estimated duration in minutes (1-1440)",
    )
    competency_level: Optional[str] = Field(
        None,
        description="Learning level: beginner, intermediate, or advanced",
    )
    language: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Content language (ISO 639-1 code, exactly 2 letters, e.g., 'de', 'en')",
    )
    format: Optional[str] = Field(
        None,
        description="Content format: video, text, quiz, interactive, or mixed",
    )
    category_ids: Optional[list[UUID]] = Field(
        None,
        max_length=5,
        description="Category UUIDs to assign (max 5)",
    )
    license: Optional[str] = Field(
        None,
        description="Content license: CC-BY, CC-BY-SA, CC0, or proprietary",
    )

    @field_validator("competency_level")
    @classmethod
    def validate_competency_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate competency_level is one of allowed values."""
        if v is None:
            return v
        allowed = ["beginner", "intermediate", "advanced"]
        if v.lower() not in allowed:
            raise ValueError(f"competency_level must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate format is one of allowed values."""
        if v is None:
            return v
        allowed = ["video", "text", "quiz", "interactive", "mixed"]
        if v.lower() not in allowed:
            raise ValueError(f"format must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("license")
    @classmethod
    def validate_license(cls, v: Optional[str]) -> Optional[str]:
        """Validate license is one of allowed values."""
        if v is None:
            return v
        allowed = ["CC-BY", "CC-BY-SA", "CC0", "proprietary"]
        if v not in allowed:
            raise ValueError(f"license must be one of: {', '.join(allowed)}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code format."""
        if v is None:
            return v
        # Normalize to lowercase and validate ISO 639-1 format (two-letter, alphabetic)
        code = v.lower()
        if len(code) != 2 or not code.isalpha():
            raise ValueError(
                "language must be a valid ISO 639-1 code (two lowercase letters, e.g., 'de', 'en')"
            )
        return code

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, v: Optional[list[UUID]]) -> Optional[list[UUID]]:
        """Validate category_ids list has max 5 items."""
        if v is not None and len(v) > 5:
            raise ValueError("Maximum 5 categories allowed")
        return v


class NanoCategoryResponse(BaseModel):
    """
    Response schema for a category assignment.

    Attributes:
        id: Category UUID
        name: Category name
        rank: Display order/priority
    """

    id: UUID = Field(..., description="Category UUID")
    name: str = Field(..., description="Category name")
    rank: int = Field(default=0, description="Display order/priority")


class NanoMetadataResponse(BaseModel):
    """
    Response schema for Nano metadata.

    Attributes:
        nano_id: Unique identifier for the Nano
        creator_id: Creator/owner UUID
        title: Nano title
        description: Detailed description
        duration_minutes: Estimated duration
        competency_level: Learning level
        language: Content language
        format: Content format/type
        status: Publishing status
        version: Semantic version
        categories: Assigned categories
        license: Content license
        thumbnail_url: Thumbnail image URL
        uploaded_at: Upload timestamp
        published_at: Publication timestamp
        updated_at: Last update timestamp
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    creator_id: UUID = Field(..., description="Creator/owner UUID")
    title: str = Field(..., description="Nano title")
    description: Optional[str] = Field(None, description="Detailed description")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    competency_level: str = Field(..., description="Learning level")
    language: str = Field(..., description="Content language (ISO 639-1)")
    format: str = Field(..., description="Content format/type")
    status: str = Field(..., description="Publishing status")
    version: str = Field(..., description="Semantic version")
    categories: list[NanoCategoryResponse] = Field(
        default_factory=list, description="Assigned categories"
    )
    license: str = Field(..., description="Content license")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class NanoDetailMetadata(BaseModel):
    """Metadata block for Nano detail view response."""

    description: Optional[str] = Field(None, description="Detailed description")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    competency_level: str = Field(..., description="Learning level")
    language: str = Field(..., description="Content language (ISO 639-1)")
    format: str = Field(..., description="Content format/type")
    status: str = Field(..., description="Publishing status")
    version: str = Field(..., description="Semantic version")
    categories: list[NanoCategoryResponse] = Field(
        default_factory=list,
        description="Assigned categories",
    )
    license: str = Field(..., description="Content license")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class NanoDetailCreator(BaseModel):
    """Creator information block for Nano detail view response."""

    id: UUID = Field(..., description="Creator/owner UUID")
    username: Optional[str] = Field(None, description="Creator username")


class NanoRatingSummary(BaseModel):
    """Aggregated rating and download summary for Nano detail view response."""

    average_rating: Decimal = Field(description="Average rating (0.00-5.00)")
    rating_count: int = Field(ge=0, description="Total number of ratings")
    download_count: int = Field(ge=0, description="Total number of downloads")


class NanoRatingUpsertRequest(BaseModel):
    """Request payload for creating or updating a 1-5 star rating."""

    score: int = Field(ge=1, le=5, description="Star score between 1 and 5")


class NanoRatingDistributionItem(BaseModel):
    """One bucket in the star-rating distribution."""

    score: int = Field(ge=1, le=5, description="Star score bucket")
    count: int = Field(ge=0, description="Number of votes in this bucket")


class NanoRatingAggregation(BaseModel):
    """Aggregated rating metrics for a Nano."""

    average_rating: Decimal = Field(description="Average rating (0.00-5.00)")
    median_rating: Decimal = Field(description="Median rating (0.00-5.00)")
    rating_count: int = Field(ge=0, description="Total number of ratings")
    distribution: list[NanoRatingDistributionItem] = Field(
        default_factory=list,
        description="Distribution across rating buckets 1-5",
    )


class NanoUserRating(BaseModel):
    """Current authenticated user's rating for a Nano."""

    rating_id: UUID = Field(..., description="Unique identifier of the rating")
    score: int = Field(ge=1, le=5, description="User's submitted star score")
    moderation_status: str = Field(description="Moderation status of the rating")
    updated_at: datetime = Field(description="Timestamp of the latest rating update")


class NanoRatingReadResponse(BaseModel):
    """Read response for Nano rating metrics."""

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    aggregation: NanoRatingAggregation = Field(description="Aggregated rating metrics")
    current_user_rating: Optional[NanoUserRating] = Field(
        None,
        description="Current user's rating, if authenticated and present",
    )


class NanoRatingMutationResponse(BaseModel):
    """Response payload for create/update rating operations."""

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    user_rating: NanoUserRating = Field(description="Current user's rating after mutation")
    aggregation: NanoRatingAggregation = Field(description="Updated aggregated rating metrics")


class NanoCommentUpsertRequest(BaseModel):
    """Request payload for creating or updating a Nano comment/review."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Comment content (1-1000 characters)",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, value: str) -> str:
        """Ensure content is not empty after trimming whitespace."""
        if not value.strip():
            raise ValueError("content must not be empty")
        return value


class NanoCommentItem(BaseModel):
    """One comment item in Nano comments responses."""

    comment_id: UUID = Field(..., description="Unique identifier for the comment")
    nano_id: UUID = Field(..., description="Nano identifier")
    user_id: UUID = Field(..., description="Author user identifier")
    username: Optional[str] = Field(None, description="Author username")
    content: str = Field(..., description="Sanitized comment content")
    moderation_status: str = Field(description="Moderation status of the comment")
    created_at: datetime = Field(..., description="Comment creation timestamp")
    updated_at: datetime = Field(..., description="Comment update timestamp")
    is_edited: bool = Field(..., description="Whether the comment was edited after creation")


class FeedbackModerationRequest(BaseModel):
    """Request payload for moderating a rating or comment."""

    status: str = Field(
        ...,
        description="Target moderation status: approved or hidden",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional moderation rationale for auditability",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Allow only terminal moderation decisions via API."""
        normalized = value.lower()
        if normalized not in {"approved", "hidden"}:
            raise ValueError("status must be one of: approved, hidden")
        return normalized


class NanoCommentMutationResponse(BaseModel):
    """Response payload for comment create/update operations."""

    comment: NanoCommentItem = Field(..., description="Created or updated comment")


class NanoCommentModerationResponse(BaseModel):
    """Response payload for comment moderation actions."""

    comment: NanoCommentItem = Field(..., description="Moderated comment item")


class NanoCommentListResponse(BaseModel):
    """Response payload for paginated Nano comments listing."""

    comments: list[NanoCommentItem] = Field(default_factory=list, description="List of comments")
    pagination: "PaginationMeta" = Field(..., description="Pagination metadata")


class NanoRatingModerationItem(BaseModel):
    """Moderation-aware rating item for moderator workflows."""

    rating_id: UUID = Field(..., description="Unique identifier of the rating")
    nano_id: UUID = Field(..., description="Nano identifier")
    user_id: UUID = Field(..., description="Rating author identifier")
    username: Optional[str] = Field(None, description="Rating author username")
    score: int = Field(ge=1, le=5, description="Star score between 1 and 5")
    moderation_status: str = Field(description="Moderation status of the rating")
    moderation_reason: Optional[str] = Field(
        None,
        description="Optional reason for the latest moderation decision",
    )
    created_at: datetime = Field(..., description="Rating creation timestamp")
    updated_at: datetime = Field(..., description="Rating update timestamp")


class NanoRatingModerationResponse(BaseModel):
    """Response payload for rating moderation actions."""

    rating: NanoRatingModerationItem = Field(description="Moderated rating item")


class NanoDownloadInfo(BaseModel):
    """Download access information for Nano detail view response."""

    requires_authentication: bool = Field(
        default=True,
        description="Whether authentication is required to download the Nano",
    )
    can_download: bool = Field(description="Whether the current caller can download the Nano")
    download_path: Optional[str] = Field(None, description="Resolved internal download path")


class NanoDetailData(BaseModel):
    """Main data payload for Nano detail view endpoint."""

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    title: str = Field(..., description="Nano title")
    metadata: NanoDetailMetadata = Field(description="Detailed metadata for Nano detail page")
    creator: NanoDetailCreator = Field(description="Creator information")
    rating_summary: NanoRatingSummary = Field(description="Aggregated rating and download metrics")
    download_info: NanoDownloadInfo = Field(description="Download-related access information")


class NanoDetailMeta(BaseModel):
    """Meta block for Nano detail view response envelope."""

    visibility: str = Field(description="Visibility scope of this Nano (public/restricted)")
    request_user_id: Optional[UUID] = Field(
        None,
        description="Authenticated caller user ID, if available",
    )


class NanoDetailResponse(BaseModel):
    """Unified response envelope for Nano detail view endpoint."""

    success: bool = Field(description="Whether the request was successful")
    data: NanoDetailData = Field(description="Nano detail payload")
    meta: NanoDetailMeta = Field(description="Response metadata")
    timestamp: datetime = Field(description="ISO 8601 timestamp when the response was generated")


class NanoDownloadInfoData(BaseModel):
    """Main data payload for Nano download info endpoint."""

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    can_download: bool = Field(description="Whether the current caller is allowed to download")
    download_url: str = Field(description="Presigned download URL for the Nano file")


class NanoDownloadInfoResponse(BaseModel):
    """Unified response envelope for Nano download info endpoint."""

    success: bool = Field(description="Whether the request was successful")
    data: NanoDownloadInfoData = Field(description="Download info payload")
    meta: NanoDetailMeta = Field(description="Response metadata")
    timestamp: datetime = Field(description="ISO 8601 timestamp when the response was generated")


class MetadataUpdateResponse(BaseModel):
    """
    Response schema for successful metadata update.

    Attributes:
        nano_id: Unique identifier for the updated Nano
        status: Current status of the Nano
        message: Success message
        updated_fields: List of fields that were updated
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    status: str = Field(..., description="Current Nano status")
    message: str = Field(default="Metadata updated successfully", description="Success message")
    updated_fields: list[str] = Field(default_factory=list, description="Fields that were updated")


class StatusUpdateRequest(BaseModel):
    """
    Request schema for updating Nano status.

    Attributes:
        status: Target status (draft/pending_review/published/archived/deleted)
        reason: Optional reason for status change (used for audit logging)
    """

    status: str = Field(
        ...,
        description="Target status: draft, pending_review, published, archived, or deleted",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for status change (for audit log)",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        allowed = ["draft", "pending_review", "published", "archived", "deleted"]
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v.lower()


class StatusUpdateResponse(BaseModel):
    """
    Response schema for successful status update.

    Attributes:
        nano_id: Unique identifier for the Nano
        old_status: Previous status
        new_status: Updated status
        message: Success message
        published_at: Publication timestamp (set when transitioning to published)
        archived_at: Archive timestamp (set when transitioning to archived)
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    old_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="Updated status")
    message: str = Field(default="Status updated successfully", description="Success message")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")


class CreatorNanoListItem(BaseModel):
    """
    Response schema for a Nano item in creator's dashboard list.

    Attributes:
        nano_id: Unique identifier for the Nano
        title: Nano title
        description: Brief description
        status: Publishing status
        thumbnail_url: Thumbnail image URL
        duration_minutes: Estimated duration
        competency_level: Learning level
        created_at: Upload/creation timestamp
        updated_at: Last update timestamp
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    title: str = Field(..., description="Nano title")
    description: Optional[str] = Field(None, description="Brief description")
    status: str = Field(..., description="Publishing status")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    competency_level: str = Field(..., description="Learning level")
    created_at: datetime = Field(..., description="Upload/creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    current_page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Results per page")
    total_results: int = Field(..., ge=0, description="Total number of results")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next_page: bool = Field(..., description="Whether there is a next page")
    has_prev_page: bool = Field(..., description="Whether there is a previous page")


class CreatorNanoListResponse(BaseModel):
    """
    Response schema for creator's Nano list endpoint.

    Attributes:
        nanos: List of Nano items
        pagination: Pagination metadata
    """

    nanos: list[CreatorNanoListItem] = Field(..., description="List of Nano items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class NanoDeleteResponse(BaseModel):
    """
    Response schema for successful Nano deletion.

    Attributes:
        nano_id: Unique identifier for the deleted Nano
        status: New status after deletion
        message: Success message
    """

    nano_id: UUID = Field(..., description="Unique identifier for the deleted Nano")
    status: str = Field(..., description="New status after deletion (archived or deleted)")
    message: str = Field(..., description="Success message")


class ModeratorQueueItem(BaseModel):
    """
    Response schema for a Nano item in the moderation queue.

    Attributes:
        nano_id: Unique identifier for the Nano
        creator_id: UUID of the creator
        creator_username: Username of the creator
        title: Nano title
        description: Brief description
        status: Publishing status (always 'pending_review')
        duration_minutes: Estimated duration
        competency_level: Learning level
        language: Content language
        submitted_at: When the Nano was submitted for review (updated_at)
        created_at: Original upload/creation timestamp
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    creator_id: UUID = Field(..., description="UUID of the creator")
    creator_username: Optional[str] = Field(None, description="Username of the creator")
    title: str = Field(..., description="Nano title")
    description: Optional[str] = Field(None, description="Brief description")
    status: str = Field(..., description="Publishing status")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    competency_level: str = Field(..., description="Learning level")
    language: str = Field(..., description="Content language code")
    submitted_at: datetime = Field(..., description="When the Nano was submitted for review")
    created_at: datetime = Field(..., description="Original upload/creation timestamp")


class ModeratorQueueListResponse(BaseModel):
    """
    Response schema for the moderation queue list endpoint.

    Attributes:
        nanos: List of Nano items pending review
        pagination: Pagination metadata
    """

    nanos: list[ModeratorQueueItem] = Field(..., description="List of Nano items pending review")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
