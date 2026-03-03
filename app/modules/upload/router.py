"""
Router for Nano upload endpoints.

This module provides API endpoints for uploading Nano ZIP files with
persistent storage in MinIO object storage.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.middleware import get_current_user_id
from app.modules.upload.schemas import UploadErrorResponse, UploadFailureState, UploadResponse
from app.modules.upload.service import create_draft_nano
from app.modules.upload.storage import MinIOStorageAdapter, StorageError
from app.modules.upload.validation import validate_upload


def get_upload_router(prefix: str = "/api/v1/upload", tags: list[str] = None) -> APIRouter:
    """
    Create and configure the upload router.

    Args:
        prefix: URL prefix for all upload endpoints
        tags: OpenAPI tags for documentation

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["Upload"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.post(
        "/nano",
        response_model=UploadResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Upload a Nano ZIP file",
        description="""
        Upload a ZIP file to create a new Nano in draft status with MinIO storage.

        **Requirements:**
        - Authentication required (Bearer token)
        - File must be in ZIP format
        - Maximum file size: 100 MB
        - Maximum upload operation duration: 10 minutes
        - ZIP must contain at least one supported file (`.pdf`, `.jpg`, `.png`, `.mp4`, `.webm`)

        **Process:**
        1. File is validated (type, size, structure)
        2. File is uploaded to MinIO object storage (private ACL)
        3. Nano record created with storage reference
        4. Upload identifier returned for metadata completion

        **Storage:**
        - Files stored in MinIO bucket with deterministic path: `nanos/{nano_id}/content/{filename}`
        - Private access control enforced
        - Metadata links object key to Nano record

        **Next Steps:**
        After successful upload, use the returned `nano_id` to:
        - Add metadata (title, description, duration, etc.) - Story 2.2
        - Publish the Nano - Story 2.4
        """,
        responses={
            201: {
                "description": "Upload successful, Nano created in draft status",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "draft",
                            "title": "My Learning Module",
                            "uploaded_at": "2026-03-02T20:30:00Z",
                            "message": "Upload successful",
                        }
                    }
                },
            },
            400: {
                "description": "Invalid file format, corrupt ZIP, or validation failure",
                "content": {
                    "application/json": {
                        "examples": {
                            "wrong_type": {
                                "summary": "Wrong file type",
                                "value": {
                                    "detail": "Invalid file type: application/pdf. Only ZIP files are accepted."
                                },
                            },
                            "corrupt_zip": {
                                "summary": "Corrupt ZIP file",
                                "value": {
                                    "detail": "Invalid ZIP file format. The file may be corrupt."
                                },
                            },
                            "empty_zip": {
                                "summary": "Empty ZIP file",
                                "value": {
                                    "detail": "ZIP file is empty. At least one file is required."
                                },
                            },
                            "unsupported_content": {
                                "summary": "ZIP without supported content",
                                "value": {
                                    "detail": "ZIP file does not contain supported content files. Supported file types: .pdf, .jpg, .png, .mp4, .webm."
                                },
                            },
                        }
                    }
                },
            },
            401: {
                "description": "Authentication required or invalid token",
                "content": {
                    "application/json": {"example": {"detail": "Missing authentication token"}}
                },
            },
            413: {
                "description": "File size exceeds maximum limit",
                "content": {
                    "application/json": {
                        "example": {"detail": "File size exceeds maximum allowed size of 100 MB."}
                    }
                },
            },
            503: {
                "description": "Object storage (MinIO) temporarily unavailable",
                "model": UploadErrorResponse,
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Object storage temporarily unavailable due to transient failure.",
                            "error_code": "UPLOAD_TRANSIENT_FAILURE",
                            "failure_state": "failed",
                            "retryable": True,
                            "retry_after_seconds": 30,
                        }
                    }
                },
            },
        },
    )
    async def upload_nano(
        file: Annotated[UploadFile, File(description="ZIP file containing Nano content")],
        db: Annotated[AsyncSession, Depends(get_db)],
        user_id: Annotated[UUID, Depends(get_current_user_id)],
    ) -> UploadResponse:
        """
        Upload a ZIP file and create a draft Nano record with object storage.

        This endpoint handles the complete upload workflow:
        1. Validates file type, size, and structure
        2. Uploads file to MinIO object storage (private ACL)
        3. Creates Nano record with file_storage_path reference
        4. Returns nano_id and status for next steps

        Args:
            file: Uploaded ZIP file
            db: Database session
            user_id: ID of authenticated user (from JWT token)

        Returns:
            UploadResponse with nano_id and status information

        Raises:
            HTTPException: For validation failures, storage errors, or database errors
        """
        # Validate uploaded file
        try:
            await validate_upload(file)
        except HTTPException:
            # Re-raise validation errors as-is
            raise

        # Create draft Nano record with MinIO storage integration
        try:
            storage_adapter = MinIOStorageAdapter()
            nano = await create_draft_nano(
                db=db,
                creator_id=user_id,
                file=file,
                storage_adapter=storage_adapter,
            )
        except StorageError as e:
            # Storage failure - return recoverable error with explicit failure state
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                headers={"Retry-After": "30"},
                content=UploadErrorResponse(
                    detail=f"Object storage temporarily unavailable due to transient failure: {str(e)}",
                    error_code="UPLOAD_TRANSIENT_FAILURE",
                    failure_state=UploadFailureState.FAILED.value,
                    retryable=True,
                    retry_after_seconds=30,
                ).model_dump(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Nano record. Please try again.",
            )

        # Return success response
        return UploadResponse(
            nano_id=nano.id,
            status=nano.status.value,
            title=nano.title,
            uploaded_at=nano.uploaded_at,
            message="Upload successful. Nano created in draft status and persisted to storage.",
        )

    return router
