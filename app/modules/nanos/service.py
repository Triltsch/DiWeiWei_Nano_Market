"""
Business logic for Nano metadata management.

This module provides service functions for creating, reading, and updating
Nano metadata with proper validation and authorization checks.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Category,
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoCategoryAssignment,
    NanoFormat,
    NanoStatus,
)
from app.modules.nanos.schemas import (
    MetadataUpdateRequest,
    NanoCategoryResponse,
    NanoMetadataResponse,
)


async def get_nano_metadata(nano_id: UUID, db: AsyncSession) -> NanoMetadataResponse:
    """
    Retrieve full metadata for a Nano.

    Args:
        nano_id: UUID of the Nano to retrieve
        db: Database session

    Returns:
        NanoMetadataResponse with full metadata

    Raises:
        HTTPException: 404 if Nano not found
    """
    # Query Nano
    stmt = select(Nano).where(Nano.id == nano_id)
    result = await db.execute(stmt)
    nano = result.scalar_one_or_none()

    if not nano:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nano with ID {nano_id} not found",
        )

    # Load category assignments with categories in a single joined query
    assignments_stmt = (
        select(NanoCategoryAssignment, Category)
        .join(Category, NanoCategoryAssignment.category_id == Category.id)
        .where(NanoCategoryAssignment.nano_id == nano_id)
        .order_by(NanoCategoryAssignment.rank)
    )
    assignments_result = await db.execute(assignments_stmt)
    assignment_category_rows = assignments_result.all()

    category_responses = [
        NanoCategoryResponse(
            id=category.id,
            name=category.name,
            rank=assignment.rank,
        )
        for assignment, category in assignment_category_rows
        if category is not None
    ]

    # Map enum values to lowercase strings for API response
    competency_level_map = {
        CompetencyLevel.BASIC: "beginner",
        CompetencyLevel.INTERMEDIATE: "intermediate",
        CompetencyLevel.ADVANCED: "advanced",
    }

    return NanoMetadataResponse(
        nano_id=nano.id,
        creator_id=nano.creator_id,
        title=nano.title,
        description=nano.description,
        duration_minutes=nano.duration_minutes,
        competency_level=competency_level_map.get(nano.competency_level, "beginner"),
        language=nano.language,
        format=nano.format.value.lower(),
        status=nano.status.value.lower(),
        version=nano.version,
        categories=category_responses,
        license=nano.license.value,
        thumbnail_url=nano.thumbnail_url,
        uploaded_at=nano.uploaded_at,
        published_at=nano.published_at,
        updated_at=nano.updated_at,
    )


async def update_nano_metadata(
    nano_id: UUID,
    metadata: MetadataUpdateRequest,
    current_user_id: UUID,
    db: AsyncSession,
) -> tuple[Nano, list[str]]:
    """
    Update Nano metadata with validation.

    Args:
        nano_id: UUID of the Nano to update
        metadata: Metadata update request
        current_user_id: UUID of the authenticated user
        db: Database session

    Returns:
        Tuple of (updated Nano, list of updated field names)

    Raises:
        HTTPException: 404 if Nano not found, 403 if not creator, 400 if invalid state
    """
    # Fetch the Nano
    stmt = select(Nano).where(Nano.id == nano_id)
    result = await db.execute(stmt)
    nano = result.scalar_one_or_none()

    if not nano:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nano with ID {nano_id} not found",
        )

    # Authorization check: only creator can update
    if nano.creator_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can update Nano metadata",
        )

    # Business rule: metadata can only be edited for draft Nanos
    if nano.status != NanoStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update metadata for Nano in '{nano.status.value}' status. Only draft Nanos can be edited.",
        )

    # Track which fields are being updated
    updated_fields = []
    fields_set = metadata.model_fields_set

    # Update basic fields (check if field was provided, even if None)
    if "title" in fields_set:
        nano.title = metadata.title
        updated_fields.append("title")

    if "description" in fields_set:
        nano.description = metadata.description
        updated_fields.append("description")

    if "duration_minutes" in fields_set:
        nano.duration_minutes = metadata.duration_minutes
        updated_fields.append("duration_minutes")

    if "language" in fields_set:
        nano.language = metadata.language
        updated_fields.append("language")

    # Update enum fields with mapping (check if field was provided, even if None)
    if "competency_level" in fields_set:
        level_map = {
            "beginner": CompetencyLevel.BASIC,
            "intermediate": CompetencyLevel.INTERMEDIATE,
            "advanced": CompetencyLevel.ADVANCED,
        }
        nano.competency_level = level_map[metadata.competency_level]
        updated_fields.append("competency_level")

    if "format" in fields_set:
        format_map = {
            "video": NanoFormat.VIDEO,
            "text": NanoFormat.TEXT,
            "quiz": NanoFormat.QUIZ,
            "interactive": NanoFormat.INTERACTIVE,
            "mixed": NanoFormat.MIXED,
        }
        nano.format = format_map[metadata.format]
        updated_fields.append("format")

    if "license" in fields_set:
        license_map = {
            "CC-BY": LicenseType.CC_BY,
            "CC-BY-SA": LicenseType.CC_BY_SA,
            "CC0": LicenseType.CC0,
            "proprietary": LicenseType.PROPRIETARY,
        }
        nano.license = license_map[metadata.license]
        updated_fields.append("license")

    # Handle category assignments
    if "category_ids" in fields_set:
        # Validate all categories exist with a single query to avoid N+1 lookups
        cat_stmt = select(Category.id).where(Category.id.in_(metadata.category_ids))
        cat_result = await db.execute(cat_stmt)
        existing_category_ids = set(cat_result.scalars().all())

        missing_ids = set(metadata.category_ids) - existing_category_ids
        if missing_ids:
            missing_str = ", ".join(str(missing_id) for missing_id in sorted(missing_ids))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID(s) {missing_str} not found",
            )

        # Delete existing category assignments
        delete_stmt = select(NanoCategoryAssignment).where(
            NanoCategoryAssignment.nano_id == nano_id
        )
        delete_result = await db.execute(delete_stmt)
        for assignment in delete_result.scalars():
            await db.delete(assignment)

        # Create new assignments
        for idx, cat_id in enumerate(metadata.category_ids):
            assignment = NanoCategoryAssignment(
                nano_id=nano_id,
                category_id=cat_id,
                rank=idx,
            )
            db.add(assignment)

        updated_fields.append("categories")

    # Commit changes
    await db.commit()
    await db.refresh(nano)

    return nano, updated_fields
