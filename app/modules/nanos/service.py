"""
Business logic for Nano metadata management.

This module provides service functions for creating, reading, and updating
Nano metadata with proper validation and authorization checks.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditAction,
    Category,
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoCategoryAssignment,
    NanoFormat,
    NanoStatus,
)
from app.modules.audit.service import AuditLogger
from app.modules.nanos.schemas import (
    MetadataUpdateRequest,
    NanoCategoryResponse,
    NanoMetadataResponse,
    StatusUpdateRequest,
)
from app.modules.search.service import invalidate_search_cache


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
        # Title is NOT NULL in DB - reject explicit None
        if metadata.title is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="title cannot be set to null (required field)",
            )
        nano.title = metadata.title
        updated_fields.append("title")

    if "description" in fields_set:
        nano.description = metadata.description
        updated_fields.append("description")

    if "duration_minutes" in fields_set:
        nano.duration_minutes = metadata.duration_minutes
        updated_fields.append("duration_minutes")

    if "language" in fields_set:
        # Language is NOT NULL in DB - reject explicit None
        if metadata.language is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="language cannot be set to null (required field)",
            )
        nano.language = metadata.language
        updated_fields.append("language")

    # Update enum fields with mapping (check if field was provided, even if None)
    if "competency_level" in fields_set:
        if metadata.competency_level is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="competency_level cannot be set to null",
            )
        level_map = {
            "beginner": CompetencyLevel.BASIC,
            "intermediate": CompetencyLevel.INTERMEDIATE,
            "advanced": CompetencyLevel.ADVANCED,
        }
        nano.competency_level = level_map[metadata.competency_level]
        updated_fields.append("competency_level")

    if "format" in fields_set:
        if metadata.format is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="format cannot be set to null",
            )
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
        if metadata.license is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="license cannot be set to null",
            )
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
        if metadata.category_ids is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category_ids cannot be set to null (use empty list to clear)",
            )

        # Deduplicate category_ids while preserving order
        seen = set()
        unique_category_ids = []
        for cat_id in metadata.category_ids:
            if cat_id not in seen:
                seen.add(cat_id)
                unique_category_ids.append(cat_id)

        # Validate all categories exist with a single query to avoid N+1 lookups
        if unique_category_ids:
            cat_stmt = select(Category.id).where(Category.id.in_(unique_category_ids))
            cat_result = await db.execute(cat_stmt)
            existing_category_ids = set(cat_result.scalars().all())

            missing_ids = set(unique_category_ids) - existing_category_ids
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

        # Create new assignments with deduplicated list
        for idx, cat_id in enumerate(unique_category_ids):
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

    # Invalidate search cache to prevent stale discovery results after metadata changes
    await invalidate_search_cache(reason="nano_metadata_updated")

    return nano, updated_fields


async def update_nano_status(
    nano_id: UUID,
    status_update: StatusUpdateRequest,
    current_user_id: UUID,
    db: AsyncSession,
) -> tuple[Nano, str, str]:
    """
    Update Nano status with state machine validation.

    Args:
        nano_id: UUID of the Nano to update
        status_update: Status update request with target status and optional reason
        current_user_id: UUID of the authenticated user
        db: Database session

    Returns:
        Tuple of (updated Nano, old_status, new_status)

    Raises:
        HTTPException: 404 if Nano not found, 403 if not creator, 400 if invalid transition
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

    # Authorization check: only creator can update status
    if nano.creator_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can update Nano status",
        )

    old_status = nano.status.value
    new_status = status_update.status

    # No-op: if status is already the target status, return immediately
    if old_status == new_status:
        return nano, old_status, new_status

    # Map string status to enum
    status_map = {
        "draft": NanoStatus.DRAFT,
        "pending_review": NanoStatus.PENDING_REVIEW,
        "published": NanoStatus.PUBLISHED,
        "archived": NanoStatus.ARCHIVED,
        "deleted": NanoStatus.DELETED,
    }
    target_status_enum = status_map[new_status]

    # State machine validation
    _validate_status_transition(nano, old_status, new_status)

    # Metadata completeness check for draft → published
    if new_status == "published" and old_status == "draft":
        _validate_metadata_completeness(nano)

    # Update status and set timestamps
    nano.status = target_status_enum

    if new_status == "published" and nano.published_at is None:
        nano.published_at = datetime.now(timezone.utc)

    if new_status == "archived" and nano.archived_at is None:
        nano.archived_at = datetime.now(timezone.utc)

    # Commit changes
    await db.commit()
    await db.refresh(nano)

    # Log status change to audit log
    await AuditLogger.log_action(
        session=db,
        action=AuditAction.DATA_MODIFIED,
        user_id=current_user_id,
        resource_type="nano",
        resource_id=str(nano_id),
        metadata={
            "field": "status",
            "old_value": old_status,
            "new_value": new_status,
            "reason": status_update.reason,
        },
    )

    # Commit audit log changes to ensure they persist beyond request scope
    await db.commit()

    # Invalidate search cache because status changes affect search visibility
    await invalidate_search_cache(reason="nano_status_updated")

    return nano, old_status, new_status


def _validate_status_transition(nano: Nano, old_status: str, new_status: str) -> None:
    """
    Validate that the status transition is allowed by the state machine.

    Allowed transitions:
    - draft → pending_review, published, archived, deleted
    - pending_review → draft, published, archived
    - published → archived, or draft (draft transition only within 24h of publication)
    - archived → deleted
    - deleted → (no transitions allowed)

    Args:
        nano: The Nano object
        old_status: Current status
        new_status: Target status

    Raises:
        HTTPException: 400 if transition is not allowed
    """
    # Define allowed transitions
    allowed_transitions = {
        "draft": ["pending_review", "published", "archived", "deleted"],
        "pending_review": ["draft", "published", "archived"],
        "published": ["archived", "draft"],  # draft only within 24h
        "archived": ["deleted"],
        "deleted": [],  # No transitions from deleted
    }

    if new_status not in allowed_transitions.get(old_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: cannot change from '{old_status}' to '{new_status}'",
        )

    # Special rule: published → draft only allowed within 24h of publication
    if old_status == "published" and new_status == "draft":
        if nano.published_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unpublish: publication timestamp is missing",
            )

        # Ensure published_at is timezone-aware for comparison
        published_at = nano.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        time_since_publish = datetime.now(timezone.utc) - published_at
        if time_since_publish.total_seconds() > 24 * 3600:  # 24 hours in seconds
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unpublish: Nano has been published for more than 24 hours. Use 'archived' status instead.",
            )


def _validate_metadata_completeness(nano: Nano) -> None:
    """
    Validate that all required metadata is complete before publishing.

    Args:
        nano: The Nano object to validate

    Raises:
        HTTPException: 400 if metadata is incomplete
    """
    missing_fields = []

    if not nano.title or nano.title.strip() == "":
        missing_fields.append("title")

    if not nano.description or nano.description.strip() == "":
        missing_fields.append("description")

    if nano.duration_minutes is None or nano.duration_minutes <= 0:
        missing_fields.append("duration_minutes")

    if not nano.language:
        missing_fields.append("language")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish: missing required metadata fields: {', '.join(missing_fields)}",
        )
