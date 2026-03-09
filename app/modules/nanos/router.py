"""
Router for Nano metadata endpoints.

This module provides API endpoints for managing Nano metadata, including
creating, reading, and updating metadata for learning content.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.middleware import get_current_user_id
from app.modules.nanos.schemas import (
    MetadataUpdateRequest,
    MetadataUpdateResponse,
    NanoMetadataResponse,
)
from app.modules.nanos.service import get_nano_metadata, update_nano_metadata


def get_nanos_router(prefix: str = "/api/v1/nanos", tags: list[str] | None = None) -> APIRouter:
    """
    Create and configure the nanos router.

    Args:
        prefix: URL prefix for all nanos endpoints
        tags: OpenAPI tags for documentation

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["Nanos"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(
        "/{nano_id}",
        response_model=NanoMetadataResponse,
        summary="Get Nano metadata",
        description="""
        Retrieve full metadata for a Nano by its ID.

        **Returns:**
        - Nano metadata including title, description, categories, status, etc.

        **Error Cases:**
        - 404: Nano not found
        """,
        responses={
            200: {
                "description": "Nano metadata retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "creator_id": "987e6543-e21b-12d3-a456-426614174000",
                            "title": "Introduction to Python",
                            "description": "Learn Python basics in 30 minutes",
                            "duration_minutes": 30,
                            "competency_level": "beginner",
                            "language": "de",
                            "format": "video",
                            "status": "draft",
                            "version": "1.0.0",
                            "categories": [
                                {
                                    "id": "456e7890-e12b-34d5-a678-901234567890",
                                    "name": "Programming",
                                    "rank": 0,
                                }
                            ],
                            "license": "CC-BY",
                            "uploaded_at": "2026-03-08T10:00:00Z",
                            "updated_at": "2026-03-08T10:00:00Z",
                        }
                    }
                },
            },
            404: {"description": "Nano not found"},
        },
    )
    async def get_nano(
        nano_id: UUID,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoMetadataResponse:
        """Get Nano metadata by ID."""
        return await get_nano_metadata(nano_id, db)

    @router.post(
        "/{nano_id}/metadata",
        response_model=MetadataUpdateResponse,
        status_code=status.HTTP_200_OK,
        summary="Update Nano metadata",
        description="""
        Update metadata for a Nano in draft status.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must be the creator of the Nano
        - Nano must be in draft status (published Nanos have immutable metadata)
        - At least one field must be provided

        **Validation:**
        - title: 1-200 characters
        - description: max 2000 characters
        - duration_minutes: 1-1440 (positive, max 24 hours)
        - competency_level: beginner, intermediate, or advanced
        - language: ISO 639-1 code (2-5 chars)
        - format: video, text, quiz, interactive, or mixed
        - category_ids: max 5 categories (must exist in database)
        - license: CC-BY, CC-BY-SA, CC0, or proprietary

        **Business Rules:**
        - Only draft Nanos can be edited
        - Published Nanos have immutable metadata
        - Only the creator can update metadata

        **Error Cases:**
        - 400: Invalid data, Nano not in draft status
        - 401: Not authenticated
        - 403: Not the creator
        - 404: Nano or category not found
        """,
        responses={
            200: {
                "description": "Metadata updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "draft",
                            "message": "Metadata updated successfully",
                            "updated_fields": ["title", "description", "duration_minutes"],
                        }
                    }
                },
            },
            400: {"description": "Invalid data or Nano not in draft status"},
            401: {"description": "Not authenticated"},
            403: {"description": "Not authorized (not the creator)"},
            404: {"description": "Nano or category not found"},
        },
    )
    async def update_metadata(
        nano_id: UUID,
        metadata: MetadataUpdateRequest,
        current_user_id: Annotated[UUID, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> MetadataUpdateResponse:
        """Update Nano metadata."""
        # Validate at least one field is provided (use model_fields_set to detect provided fields)
        if not metadata.model_fields_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        nano, updated_fields = await update_nano_metadata(nano_id, metadata, current_user_id, db)

        return MetadataUpdateResponse(
            nano_id=nano.id,
            status=nano.status.value.lower(),
            message="Metadata updated successfully",
            updated_fields=updated_fields,
        )

    return router
