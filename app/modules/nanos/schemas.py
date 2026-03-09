"""
Pydantic schemas for Nano metadata operations.

This module defines request and response models for the Nano metadata API endpoints.
"""

from datetime import datetime
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
        max_length=5,
        description="Content language (ISO 639-1, e.g., 'de', 'en')",
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
