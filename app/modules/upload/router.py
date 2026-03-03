"""
Router for Nano upload endpoints.

This module provides API endpoints for uploading Nano ZIP files.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.middleware import get_current_user_id
from app.modules.upload.schemas import UploadResponse
from app.modules.upload.service import create_draft_nano
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
        Upload a ZIP file to create a new Nano in draft status.

        **Requirements:**
        - Authentication required (Bearer token)
        - File must be in ZIP format
        - Maximum file size: 100 MB
        - ZIP must contain at least one supported file (`.pdf`, `.jpg`, `.png`, `.mp4`, `.webm`)

        **Process:**
        1. File is validated (type, size, structure)
        2. Nano record created with status "draft"
        3. Upload identifier returned for metadata completion

        **Next Steps:**
        After successful upload, use the returned `nano_id` to:
        - Add metadata (title, description, etc.) - Story 2.2
        - Upload to object storage (MinIO) - Story 7.3 (S2-BE-04)
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
        },
    )
    async def upload_nano(
        file: Annotated[UploadFile, File(description="ZIP file containing Nano content")],
        db: Annotated[AsyncSession, Depends(get_db)],
        user_id: Annotated[UUID, Depends(get_current_user_id)],
    ) -> UploadResponse:
        """
        Upload a ZIP file and create a draft Nano record.

        This endpoint handles the initial upload phase of the Nano creation workflow.
        The uploaded file is validated but not yet stored in object storage (MinIO).
        Storage integration will be completed in Story S2-BE-04.

        Args:
            file: Uploaded ZIP file
            db: Database session
            user_id: ID of authenticated user (from JWT token)

        Returns:
            UploadResponse with nano_id and status information

        Raises:
            HTTPException: For validation failures or database errors
        """
        # Validate uploaded file
        try:
            await validate_upload(file)
        except HTTPException:
            # Re-raise validation errors as-is
            raise

        # Create draft Nano record
        try:
            nano = await create_draft_nano(
                db=db,
                creator_id=user_id,
                file=file,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Nano record: {str(e)}",
            )

        # Return success response
        return UploadResponse(
            nano_id=nano.id,
            status=nano.status.value,
            title=nano.title,
            uploaded_at=nano.uploaded_at,
            message="Upload successful. Nano created in draft status.",
        )

    return router
