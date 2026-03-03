"""
Pydantic schemas for Nano upload operations.

This module defines request and response models for the upload API endpoints.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """
    Response schema for successful Nano upload.

    Attributes:
        nano_id: Unique identifier for the created Nano record
        status: Current status of the Nano (should be "draft")
        title: Title of the uploaded Nano
        uploaded_at: Timestamp of upload
        message: Success message
    """

    nano_id: UUID = Field(..., description="Unique identifier for the Nano")
    status: str = Field(..., description="Current Nano status (draft)")
    title: str = Field(..., description="Nano title")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    message: str = Field(default="Upload successful", description="Success message")


class UploadErrorResponse(BaseModel):
    """
    Error response schema for failed uploads.

    Attributes:
        detail: Error message describing what went wrong
        error_code: Machine-readable error code
        failure_state: Explicit upload failure state for client workflow handling
        retryable: Whether retry is recommended for this failure
        retry_after_seconds: Suggested wait time before retry, if applicable
    """

    detail: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    failure_state: str = Field(
        default="failed",
        description="Explicit upload operation state in error responses",
    )
    retryable: bool = Field(
        default=False,
        description="Whether clients should retry this upload request",
    )
    retry_after_seconds: int | None = Field(
        default=None,
        description="Recommended delay (seconds) before retrying transient failures",
    )


class UploadFailureState(str, Enum):
    """Allowed failure state values for upload error responses."""

    FAILED = "failed"


class ValidationErrorDetail(BaseModel):
    """
    Detailed validation error information.

    Attributes:
        field: Name of the field that failed validation
        message: Description of the validation failure
    """

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation error message")
