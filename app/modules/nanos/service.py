"""
Business logic for Nano metadata management.

This module provides service functions for creating, reading, and updating
Nano metadata with proper validation and authorization checks.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
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
    User,
    UserRole,
)
from app.modules.audit.service import AuditLogger
from app.modules.auth.tokens import TokenData
from app.modules.nanos.schemas import (
    CreatorNanoListItem,
    CreatorNanoListResponse,
    MetadataUpdateRequest,
    ModeratorQueueItem,
    ModeratorQueueListResponse,
    NanoCategoryResponse,
    NanoDeleteResponse,
    NanoDetailCreator,
    NanoDetailData,
    NanoDetailMeta,
    NanoDetailMetadata,
    NanoDetailResponse,
    NanoDownloadInfo,
    NanoDownloadInfoData,
    NanoDownloadInfoResponse,
    NanoMetadataResponse,
    NanoRatingSummary,
    PaginationMeta,
    StatusUpdateRequest,
)
from app.modules.search.service import invalidate_search_cache


async def get_nano_metadata(
    nano_id: UUID,
    db: AsyncSession,
    current_user: TokenData | None,
) -> NanoMetadataResponse:
    """
    Retrieve full metadata for a Nano.

    Args:
        nano_id: UUID of the Nano to retrieve
        db: Database session
        current_user: Optional authenticated caller context

    Returns:
        NanoMetadataResponse with full metadata

    Raises:
        HTTPException: 404 if Nano not found, 401/403 for visibility violations
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

    if nano.status != NanoStatus.PUBLISHED:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access non-published Nano metadata",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not _can_access_restricted_nano(nano=nano, current_user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this non-published Nano",
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


async def get_nano_detail(
    nano_id: UUID,
    db: AsyncSession,
    current_user: TokenData | None,
) -> NanoDetailResponse:
    """
    Retrieve Nano detail payload with visibility and download access rules.

    Visibility rules:
    - published: publicly visible
    - non-published: creator, admin, and moderator only

    Download rules:
    - authentication required
    - non-published downloads: creator, admin, moderator only

    Args:
        nano_id: UUID of the Nano to retrieve
        db: Database session
        current_user: Optional authenticated caller context

    Returns:
        NanoDetailResponse with unified response envelope

    Raises:
        HTTPException: 404 if Nano not found, 401/403 for visibility violations
    """
    stmt = (
        select(Nano, User.username)
        .outerjoin(User, Nano.creator_id == User.id)
        .where(Nano.id == nano_id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nano with ID {nano_id} not found",
        )

    nano, creator_username = row

    visibility = "public" if nano.status == NanoStatus.PUBLISHED else "restricted"

    if nano.status != NanoStatus.PUBLISHED:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access non-published Nano details",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not _can_access_restricted_nano(nano=nano, current_user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this non-published Nano",
            )

    category_responses = await _get_nano_categories(nano_id=nano_id, db=db)

    competency_level_map = {
        CompetencyLevel.BASIC: "beginner",
        CompetencyLevel.INTERMEDIATE: "intermediate",
        CompetencyLevel.ADVANCED: "advanced",
    }

    can_download = current_user is not None and (
        nano.status == NanoStatus.PUBLISHED
        or _can_access_restricted_nano(nano=nano, current_user=current_user)
    )

    return NanoDetailResponse(
        success=True,
        data=NanoDetailData(
            nano_id=nano.id,
            title=nano.title,
            metadata=NanoDetailMetadata(
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
            ),
            creator=NanoDetailCreator(
                id=nano.creator_id,
                username=creator_username,
            ),
            rating_summary=NanoRatingSummary(
                average_rating=nano.average_rating,
                rating_count=nano.rating_count,
                download_count=nano.download_count,
            ),
            download_info=NanoDownloadInfo(
                requires_authentication=True,
                can_download=can_download,
                download_path=nano.file_storage_path if can_download else None,
            ),
        ),
        meta=NanoDetailMeta(
            visibility=visibility,
            request_user_id=current_user.user_id if current_user else None,
        ),
        timestamp=datetime.now(timezone.utc),
    )


async def get_nano_download_info(
    nano_id: UUID,
    db: AsyncSession,
    current_user: TokenData,
) -> NanoDownloadInfoResponse:
    """
    Resolve download path for a Nano with strict authentication and RBAC checks.

    Rules:
    - authentication always required
    - published: any authenticated user can download
    - non-published: creator, admin, and moderator only

    Args:
        nano_id: UUID of the Nano to resolve download info for
        db: Database session
        current_user: Authenticated caller context

    Returns:
        NanoDownloadInfoResponse with unified response envelope

    Raises:
        HTTPException: 404 if Nano/path missing, 403 for RBAC violations
    """
    stmt = select(Nano).where(Nano.id == nano_id)
    result = await db.execute(stmt)
    nano = result.scalar_one_or_none()

    if not nano:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nano with ID {nano_id} not found",
        )

    if nano.status != NanoStatus.PUBLISHED and not _can_access_restricted_nano(
        nano=nano,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to download this non-published Nano",
        )

    if not nano.file_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download path is not available for this Nano",
        )

    visibility = "public" if nano.status == NanoStatus.PUBLISHED else "restricted"

    return NanoDownloadInfoResponse(
        success=True,
        data=NanoDownloadInfoData(
            nano_id=nano.id,
            can_download=True,
            download_path=nano.file_storage_path,
        ),
        meta=NanoDetailMeta(
            visibility=visibility,
            request_user_id=current_user.user_id,
        ),
        timestamp=datetime.now(timezone.utc),
    )


async def _get_nano_categories(nano_id: UUID, db: AsyncSession) -> list[NanoCategoryResponse]:
    """Fetch category assignments for a Nano ordered by rank."""
    assignments_stmt = (
        select(NanoCategoryAssignment, Category)
        .join(Category, NanoCategoryAssignment.category_id == Category.id)
        .where(NanoCategoryAssignment.nano_id == nano_id)
        .order_by(NanoCategoryAssignment.rank)
    )
    assignments_result = await db.execute(assignments_stmt)
    assignment_category_rows = assignments_result.all()

    return [
        NanoCategoryResponse(
            id=category.id,
            name=category.name,
            rank=assignment.rank,
        )
        for assignment, category in assignment_category_rows
        if category is not None
    ]


def _can_access_restricted_nano(nano: Nano, current_user: TokenData) -> bool:
    """Return whether caller can access non-published Nano resources."""
    if nano.creator_id == current_user.user_id:
        return True
    return current_user.role in {UserRole.ADMIN.value, UserRole.MODERATOR.value}


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
    current_user: TokenData,
    db: AsyncSession,
) -> tuple[Nano, str, str]:
    """
    Update Nano status with state machine validation.

    Args:
        nano_id: UUID of the Nano to update
        status_update: Status update request with target status and optional reason
        current_user: Authenticated user token data (used for RBAC)
        db: Database session

    Returns:
        Tuple of (updated Nano, old_status, new_status)

    Raises:
        HTTPException: 404 if Nano not found, 403 if not creator/moderator/admin, 400 if invalid transition
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

    old_status = nano.status.value
    new_status = status_update.status

    # Authorization check: must happen before all state changes (including no-op returns)
    # so that RBAC is enforced even when no transition is requested.
    is_creator = nano.creator_id == current_user.user_id
    is_moderator_or_admin = current_user.role in {UserRole.ADMIN.value, UserRole.MODERATOR.value}

    if not is_creator and not is_moderator_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator, a moderator, or an admin can update Nano status",
        )

    # Moderators/admins may only act on Nanos that are currently in pending_review;
    # this prevents acting on draft/published/archived Nanos they do not own.
    if not is_creator and is_moderator_or_admin and old_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderators can only update Nanos that are in 'pending_review' status",
        )

    # Moderators/admins reviewing someone else's Nano may only approve (→published)
    # or reject (→draft); other transitions (e.g. pending_review → archived) are
    # outside the intended moderation workflow.
    if not is_creator and is_moderator_or_admin and new_status not in {"published", "draft"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderators can only approve (status=published) or reject (status=draft) a review submission",
        )

    # Creators without moderator/admin role may not publish directly.
    # Publication requires explicit approval by a moderator or admin.
    # Moderators/admins who also own the Nano are exempt — they can self-approve
    # when they act in a moderation capacity.
    if is_creator and not is_moderator_or_admin and new_status == "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators and admins can publish Nanos after review",
        )

    # No-op: return early if the status is already the target (RBAC already enforced above).
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

    # Metadata completeness check for any transition that publishes a Nano.
    if new_status == "published":
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
        user_id=current_user.user_id,
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


async def get_creator_nanos(
    creator_id: UUID,
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = None,
) -> CreatorNanoListResponse:
    """
    Get list of Nanos owned by a creator with pagination.

    Args:
        creator_id: UUID of the creator
        db: Database session
        page: Page number (1-indexed), defaults to 1
        limit: Results per page, defaults to 20, max 100
        status_filter: Optional status filter (draft, published, etc.)

    Returns:
        CreatorNanoListResponse with paginated list of creator's Nanos

    Raises:
        HTTPException: 404 if creator not found
    """
    # Validate creator exists
    creator_stmt = select(User).where(User.id == creator_id)
    creator_result = await db.execute(creator_stmt)
    creator = creator_result.scalar_one_or_none()

    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )

    # Normalize and validate status filter to NanoStatus enum.
    # A raw string comparison against an Enum column can silently return no results
    # instead of raising an error; validating early provides a clear 400 response.
    status_enum_filter: NanoStatus | None = None
    if status_filter:
        try:
            status_enum_filter = NanoStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter value: {status_filter!r}. "
                "Valid values are: draft, pending_review, published, archived, deleted.",
            ) from exc

    # Build query for creator's Nanos
    query = select(Nano).where(Nano.creator_id == creator_id)

    # Apply status filter if provided and validated
    if status_enum_filter is not None:
        query = query.where(Nano.status == status_enum_filter)

    # Count total results
    count_query = select(func.count(Nano.id)).where(Nano.creator_id == creator_id)
    if status_enum_filter is not None:
        count_query = count_query.where(Nano.status == status_enum_filter)

    count_result = await db.execute(count_query)
    total_results = count_result.scalar() or 0

    # Calculate pagination
    total_pages = (total_results + limit - 1) // limit if limit > 0 else 1
    offset = (page - 1) * limit

    # Fetch paginated results ordered by updated_at descending
    query = query.order_by(desc(Nano.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    nanos = result.scalars().all()

    # Convert to response items
    nano_items = [
        CreatorNanoListItem(
            nano_id=nano.id,
            title=nano.title,
            description=nano.description,
            status=nano.status.value.lower(),
            thumbnail_url=nano.thumbnail_url,
            duration_minutes=nano.duration_minutes,
            competency_level=nano.competency_level.name.lower(),
            created_at=nano.uploaded_at,
            updated_at=nano.updated_at,
        )
        for nano in nanos
    ]

    # Build pagination metadata
    pagination = PaginationMeta(
        current_page=page,
        page_size=limit,
        total_results=total_results,
        total_pages=total_pages,
        has_next_page=page < total_pages,
        has_prev_page=page > 1,
    )

    return CreatorNanoListResponse(nanos=nano_items, pagination=pagination)


async def delete_nano(
    nano_id: UUID,
    creator_id: UUID,
    db: AsyncSession,
) -> NanoDeleteResponse:
    """
    Delete (soft-delete via archiving) a Nano.

    Business rules:
    - Only the creator can delete their own Nano
    - Only draft/archived Nanos can be deleted (not published)
    - Published Nanos must be archived first via status transition
    - Deletion is soft-delete (status = deleted)

    Args:
        nano_id: UUID of the Nano to delete
        creator_id: UUID of the requesting creator
        db: Database session

    Returns:
        NanoDeleteResponse confirming deletion

    Raises:
        HTTPException: 403 if not creator, 404 if not found, 400 if invalid state
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

    if nano.creator_id != creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this Nano",
        )

    # Verify Nano is in a deletable state.
    # Only DRAFT and ARCHIVED Nanos may be deleted; other states (published,
    # pending_review, etc.) must be resolved before deletion is allowed.
    if nano.status not in (NanoStatus.DRAFT, NanoStatus.ARCHIVED):
        if nano.status == NanoStatus.PUBLISHED:
            detail = "Cannot delete published Nano. Archive it first."
        else:
            detail = "Only draft or archived Nanos can be deleted."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    # Soft-delete: set status to deleted and persist
    old_status = nano.status.value.lower()
    nano.status = NanoStatus.DELETED
    await db.commit()
    await db.refresh(nano)

    # Invalidate search cache after the database has been updated
    await invalidate_search_cache(reason="nano_deleted")

    # Log audit event
    await AuditLogger.log_action(
        session=db,
        action=AuditAction.DATA_DELETED,
        user_id=creator_id,
        resource_type="nano",
        resource_id=str(nano_id),
        metadata={"old_status": old_status, "new_status": "deleted"},
    )
    await db.commit()

    return NanoDeleteResponse(
        nano_id=nano.id,
        status="deleted",
        message="Nano deleted successfully",
    )


async def get_pending_review_nanos(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
) -> ModeratorQueueListResponse:
    """
    Get list of all Nanos currently in `pending_review` status for the moderation queue.

    Only accessible to users with moderator or admin roles (enforced at the router layer).

    Args:
        db: Database session
        page: Page number (1-indexed), defaults to 1
        limit: Results per page, defaults to 20, max 100

    Returns:
        ModeratorQueueListResponse with paginated list of pending-review Nanos including
        creator usernames for context.
    """
    count_query = select(func.count(Nano.id)).where(Nano.status == NanoStatus.PENDING_REVIEW)
    count_result = await db.execute(count_query)
    total_results = count_result.scalar() or 0

    total_pages = (total_results + limit - 1) // limit if limit > 0 else 1
    offset = (page - 1) * limit

    query = (
        select(Nano, User.username)
        .outerjoin(User, Nano.creator_id == User.id)
        .where(Nano.status == NanoStatus.PENDING_REVIEW)
        .order_by(Nano.updated_at)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    queue_items = [
        ModeratorQueueItem(
            nano_id=nano.id,
            creator_id=nano.creator_id,
            creator_username=creator_username,
            title=nano.title,
            description=nano.description,
            status=nano.status.value.lower(),
            duration_minutes=nano.duration_minutes,
            competency_level=nano.competency_level.name.lower(),
            language=nano.language,
            submitted_at=nano.updated_at,
            created_at=nano.uploaded_at,
        )
        for nano, creator_username in rows
    ]

    pagination = PaginationMeta(
        current_page=page,
        page_size=limit,
        total_results=total_results,
        total_pages=total_pages,
        has_next_page=page < total_pages,
        has_prev_page=page > 1,
    )

    return ModeratorQueueListResponse(nanos=queue_items, pagination=pagination)
