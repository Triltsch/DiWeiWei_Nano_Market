"""
Business logic for the Moderation Queue API.

This module contains all service-layer functions for:

1. Upserting (creating or resetting) a moderation case when content enters or
   re-enters review.
2. Retrieving the paginated, filterable moderation queue.
3. Applying a moderation decision (approve / reject / defer / escalate) to a
   case and to the underlying content record in a single atomic transaction.

Design notes
------------
- ``upsert_moderation_case`` is called from the nanos service whenever content
  transitions to a reviewable state (nano → pending_review, new/updated rating,
  new/updated comment).
- ``review_moderation_case`` is the authoritative decision point.  It updates
  *both* the ModerationCase and the underlying content (Nano, NanoRating, or
  NanoComment) inside one transaction so there is no window of inconsistency.
- Audit entries use the granular ``MODERATION_APPROVED`` / ``MODERATION_REJECTED``
  / ``MODERATION_DEFERRED`` / ``MODERATION_ESCALATED`` action codes for precise
  event filtering, rather than the generic ``DATA_MODIFIED`` used by older routes.
- ``reporter_id`` on ModerationCase is intentionally left NULL by this module;
  Story 6.3 will populate it when user-submitted flags arrive.
"""

import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditAction,
    FeedbackModerationStatus,
    ModerationCase,
    ModerationCaseStatus,
    ModerationContentType,
    Nano,
    NanoComment,
    NanoRating,
    NanoStatus,
    User,
)
from app.modules.audit.service import AuditLogger
from app.modules.auth.tokens import TokenData
from app.modules.moderation.schemas import (
    VALID_DECISIONS,
    CommentContentDetail,
    ContentDetail,
    ModerationQueueItem,
    ModerationQueueResponse,
    ModerationReviewRequest,
    NanoContentDetail,
    PaginationMeta,
    RatingContentDetail,
)
from app.modules.search.service import invalidate_search_cache

logger = logging.getLogger(__name__)

# Decision → ModerationCaseStatus mapping
_DECISION_TO_CASE_STATUS: dict[str, ModerationCaseStatus] = {
    "approve": ModerationCaseStatus.APPROVED,
    "reject": ModerationCaseStatus.REJECTED,
    "defer": ModerationCaseStatus.DEFERRED,
    "escalate": ModerationCaseStatus.ESCALATED,
}

# Decision → AuditAction mapping
_DECISION_TO_AUDIT_ACTION: dict[str, AuditAction] = {
    "approve": AuditAction.MODERATION_APPROVED,
    "reject": AuditAction.MODERATION_REJECTED,
    "defer": AuditAction.MODERATION_DEFERRED,
    "escalate": AuditAction.MODERATION_ESCALATED,
}


# ---------------------------------------------------------------------------
# Case lifecycle helpers
# ---------------------------------------------------------------------------


async def upsert_moderation_case(
    db: AsyncSession,
    content_type: ModerationContentType,
    content_id: UUID,
) -> ModerationCase:
    """Create or reset a moderation case to PENDING.

    Called by the nanos service whenever content enters or re-enters review:
    - Nano transitions to ``pending_review``
    - A NanoRating is created or updated (resets moderation_status to PENDING)
    - A NanoComment is created or updated (resets moderation_status to PENDING)

    If an existing case is found it is reset to PENDING so that the review
    queue reflects the current state while the full decision history remains
    in ``audit_logs``.

    Args:
        db:           Active database session.
        content_type: Enum value identifying the content table.
        content_id:   Primary key of the reviewable content record.

    Returns:
        The freshly created or reset :class:`~app.models.ModerationCase`.
    """
    stmt = select(ModerationCase).where(
        ModerationCase.content_type == content_type,
        ModerationCase.content_id == content_id,
    )
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()

    if case is None:
        case = ModerationCase(
            content_type=content_type,
            content_id=content_id,
            status=ModerationCaseStatus.PENDING,
        )
        db.add(case)
    else:
        # Reset to PENDING, clearing all prior decision metadata.
        case.status = ModerationCaseStatus.PENDING
        case.reason = None
        case.decided_by_user_id = None
        case.decided_at = None
        case.deferred_until = None
        case.escalation_note = None

    await db.flush()
    return case


# ---------------------------------------------------------------------------
# Queue retrieval
# ---------------------------------------------------------------------------


async def get_moderation_queue(
    db: AsyncSession,
    content_type: Optional[ModerationContentType] = None,
    status_filter: Optional[ModerationCaseStatus] = ModerationCaseStatus.PENDING,
    page: int = 1,
    limit: int = 20,
) -> ModerationQueueResponse:
    """Return a paginated, filterable moderation queue.

    The queue is sorted by ``created_at`` ascending (FIFO) so that the oldest
    cases are reviewed first.

    Args:
        db:            Active database session.
        content_type:  Optional filter by content type.  Returns all types when
                       ``None``.
        status_filter: Filter by case status.  Defaults to ``PENDING`` (active
                       queue).  Pass ``None`` to include all statuses.
        page:          1-indexed page number.
        limit:         Results per page (1–100).

    Returns:
        :class:`~app.modules.moderation.schemas.ModerationQueueResponse`
    """
    # Ensure legacy pending items that were created before moderation-case upsert hooks
    # are visible in the new queue API as pending cases.
    if status_filter in {None, ModerationCaseStatus.PENDING}:
        inserted = await _backfill_missing_pending_cases(db=db, content_type=content_type)
        if inserted > 0:
            await db.commit()

    # --- Build base query ---------------------------------------------------
    base_stmt = select(ModerationCase).order_by(ModerationCase.created_at, ModerationCase.id)

    if status_filter is not None:
        base_stmt = base_stmt.where(ModerationCase.status == status_filter)

    if content_type is not None:
        base_stmt = base_stmt.where(ModerationCase.content_type == content_type)

    # --- Count total matching rows ------------------------------------------
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_results = int(await db.scalar(count_stmt) or 0)

    # --- Fetch current page -------------------------------------------------
    offset = (page - 1) * limit
    page_stmt = base_stmt.offset(offset).limit(limit)
    page_result = await db.execute(page_stmt)
    cases = page_result.scalars().all()

    total_pages = (total_results + limit - 1) // limit if limit > 0 else 1

    # --- Enrich each case with content details ------------------------------
    detail_map = await _load_content_details_for_cases(db, cases)

    items = []
    for case in cases:
        items.append(
            ModerationQueueItem(
                case_id=case.id,
                content_type=case.content_type,
                content_id=case.content_id,
                reporter_id=case.reporter_id,
                status=case.status,
                reason=case.reason,
                decided_by_user_id=case.decided_by_user_id,
                decided_at=case.decided_at,
                deferred_until=case.deferred_until,
                escalation_note=case.escalation_note,
                created_at=case.created_at,
                updated_at=case.updated_at,
                content_detail=detail_map.get((case.content_type, case.content_id)),
            )
        )

    return ModerationQueueResponse(
        items=items,
        pagination=PaginationMeta(
            current_page=page,
            page_size=limit,
            total_results=total_results,
            total_pages=total_pages,
            has_next_page=page < total_pages,
            has_prev_page=page > 1,
        ),
    )


async def _backfill_missing_pending_cases(
    *,
    db: AsyncSession,
    content_type: Optional[ModerationContentType],
) -> int:
    """Create missing pending moderation cases for already pending content.

    This keeps `/api/v1/moderation/queue` consistent with the legacy
    `/api/v1/nanos/pending-moderation` endpoint when data existed before the
    moderation-case upsert integration was deployed.
    """
    inserted = 0

    if content_type in {None, ModerationContentType.NANO}:
        pending_nano_ids = list(
            (await db.execute(select(Nano.id).where(Nano.status == NanoStatus.PENDING_REVIEW)))
            .scalars()
            .all()
        )
        inserted += await _insert_missing_cases_for_content_type(
            db=db,
            content_type=ModerationContentType.NANO,
            content_ids=pending_nano_ids,
        )

    if content_type in {None, ModerationContentType.NANO_RATING}:
        pending_rating_ids = list(
            (
                await db.execute(
                    select(NanoRating.id).where(
                        NanoRating.moderation_status == FeedbackModerationStatus.PENDING
                    )
                )
            )
            .scalars()
            .all()
        )
        inserted += await _insert_missing_cases_for_content_type(
            db=db,
            content_type=ModerationContentType.NANO_RATING,
            content_ids=pending_rating_ids,
        )

    if content_type in {None, ModerationContentType.NANO_COMMENT}:
        pending_comment_ids = list(
            (
                await db.execute(
                    select(NanoComment.id).where(
                        NanoComment.moderation_status == FeedbackModerationStatus.PENDING
                    )
                )
            )
            .scalars()
            .all()
        )
        inserted += await _insert_missing_cases_for_content_type(
            db=db,
            content_type=ModerationContentType.NANO_COMMENT,
            content_ids=pending_comment_ids,
        )

    return inserted


async def _insert_missing_cases_for_content_type(
    *,
    db: AsyncSession,
    content_type: ModerationContentType,
    content_ids: list[UUID],
) -> int:
    """Insert moderation cases for IDs that do not yet have a case."""
    if not content_ids:
        return 0

    # Restrict the lookup to only the provided content_ids to avoid a full-table
    # scan on moderation_cases (which could be very large).  The index on
    # (content_type, content_id) is used for both the IN-list check and the
    # subsequent INSERT path.
    existing_ids = set(
        (
            await db.execute(
                select(ModerationCase.content_id).where(
                    ModerationCase.content_type == content_type,
                    ModerationCase.content_id.in_(content_ids),
                )
            )
        )
        .scalars()
        .all()
    )

    missing_ids = [cid for cid in content_ids if cid not in existing_ids]
    if not missing_ids:
        return 0

    # Bulk-add all missing cases in a single flush rather than N individual
    # INSERT statements.
    db.add_all(
        [
            ModerationCase(
                content_type=content_type,
                content_id=content_id,
                status=ModerationCaseStatus.PENDING,
            )
            for content_id in missing_ids
        ]
    )
    await db.flush()
    return len(missing_ids)


async def get_moderation_case(
    db: AsyncSession,
    case_id: UUID,
) -> ModerationQueueItem:
    """Return a single moderation case by ID, enriched with content details.

    Args:
        db:      Active database session.
        case_id: UUID of the ModerationCase.

    Returns:
        :class:`~app.modules.moderation.schemas.ModerationQueueItem`

    Raises:
        HTTPException: 404 if no case with the given ID exists.
    """
    stmt = select(ModerationCase).where(ModerationCase.id == case_id)
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moderation case {case_id} not found",
        )

    detail = await _get_content_detail(db, case.content_type, case.content_id)

    return ModerationQueueItem(
        case_id=case.id,
        content_type=case.content_type,
        content_id=case.content_id,
        reporter_id=case.reporter_id,
        status=case.status,
        reason=case.reason,
        decided_by_user_id=case.decided_by_user_id,
        decided_at=case.decided_at,
        deferred_until=case.deferred_until,
        escalation_note=case.escalation_note,
        created_at=case.created_at,
        updated_at=case.updated_at,
        content_detail=detail,
    )


# ---------------------------------------------------------------------------
# Decision endpoint
# ---------------------------------------------------------------------------


async def review_moderation_case(
    db: AsyncSession,
    case_id: UUID,
    request: ModerationReviewRequest,
    decided_by: TokenData,
) -> ModerationQueueItem:
    """Apply a moderation decision to a case and update the underlying content.

    All mutations (case fields + content status + audit log) are committed as
    a single atomic transaction.

    Decision semantics per content type:

    Nano
    ~~~~
    - approve  → ``published``  (nano.status, sets ``published_at`` if unset)
    - reject   → ``draft``      (nano back to editing)
    - defer    → stay in ``pending_review``, case marked DEFERRED
    - escalate → stay in ``pending_review``, case marked ESCALATED

    NanoRating / NanoComment (feedback)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - approve  → ``approved``  (FeedbackModerationStatus), syncs rating cache
    - reject   → ``hidden``    (FeedbackModerationStatus)
    - defer    → stay PENDING, case marked DEFERRED
    - escalate → stay PENDING, case marked ESCALATED

    Args:
        db:         Active database session.
        case_id:    UUID of the ModerationCase to decide on.
        request:    Decision payload (decision, reason, deferred_until).
        decided_by: Token data of the authenticated moderator/admin.

    Returns:
        Updated :class:`~app.modules.moderation.schemas.ModerationQueueItem`.

    Raises:
        HTTPException: 404 if case not found, 422 if decision value is invalid.
    """
    # --- Validate decision --------------------------------------------------
    if not request.is_valid_decision():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Invalid decision '{request.decision}'.  "
                f"Allowed values: {', '.join(sorted(VALID_DECISIONS))}."
            ),
        )

    # --- Load case ----------------------------------------------------------
    stmt = select(ModerationCase).where(ModerationCase.id == case_id)
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moderation case {case_id} not found",
        )

    now = datetime.now(timezone.utc)

    # --- Update case fields -------------------------------------------------
    case.status = _DECISION_TO_CASE_STATUS[request.decision]
    case.reason = request.reason
    case.decided_by_user_id = decided_by.user_id
    case.decided_at = now
    case.escalation_note = request.reason if request.decision == "escalate" else None
    case.deferred_until = request.deferred_until if request.decision == "defer" else None

    # --- Apply decision to underlying content --------------------------------
    nano_visibility_changed = await _apply_decision_to_content(
        db=db,
        case=case,
        decided_by=decided_by,
        request=request,
        now=now,
    )

    # Keep moderation decisions available even when audit enum migrations lag.
    try:
        async with db.begin_nested():
            await AuditLogger.log_action(
                session=db,
                action=_DECISION_TO_AUDIT_ACTION[request.decision],
                user_id=decided_by.user_id,
                resource_type=case.content_type.value,
                resource_id=str(case.content_id),
                metadata={
                    "case_id": str(case_id),
                    "decision": request.decision,
                    "reason": request.reason,
                    "deferred_until": (
                        request.deferred_until.isoformat() if request.deferred_until else None
                    ),
                },
            )
    except SQLAlchemyError:
        logger.exception(
            "Failed to persist moderation audit event; continuing decision flow",
            extra={
                "case_id": str(case_id),
                "decision": request.decision,
                "content_type": case.content_type.value,
                "content_id": str(case.content_id),
            },
        )

    # --- Single atomic commit for case + content + audit --------------------
    await db.commit()

    # Keep search results consistent when moderation changes Nano visibility.
    if nano_visibility_changed:
        await invalidate_search_cache(reason="moderation_nano_status_reviewed")

    await db.refresh(case)

    # --- Return enriched item -----------------------------------------------
    detail = await _get_content_detail(db, case.content_type, case.content_id)

    return ModerationQueueItem(
        case_id=case.id,
        content_type=case.content_type,
        content_id=case.content_id,
        reporter_id=case.reporter_id,
        status=case.status,
        reason=case.reason,
        decided_by_user_id=case.decided_by_user_id,
        decided_at=case.decided_at,
        deferred_until=case.deferred_until,
        escalation_note=case.escalation_note,
        created_at=case.created_at,
        updated_at=case.updated_at,
        content_detail=detail,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _apply_decision_to_content(
    *,
    db: AsyncSession,
    case: ModerationCase,
    decided_by: TokenData,
    request: ModerationReviewRequest,
    now: datetime,
) -> bool:
    """Update the underlying content record based on the moderation decision.

    Modifications are flushed to the session but NOT committed here; the
    caller is responsible for the final commit.
    """
    decision = request.decision

    if case.content_type == ModerationContentType.NANO:
        return await _apply_nano_decision(db=db, case=case, decision=decision, now=now)

    elif case.content_type == ModerationContentType.NANO_RATING:
        await _apply_rating_decision(
            db=db, case=case, decided_by=decided_by, request=request, now=now
        )

    elif case.content_type == ModerationContentType.NANO_COMMENT:
        await _apply_comment_decision(
            db=db, case=case, decided_by=decided_by, request=request, now=now
        )

    # ModerationContentType.FLAG — reserved for Story 6.3; no action yet.
    return False


async def _apply_nano_decision(
    *,
    db: AsyncSession,
    case: ModerationCase,
    decision: str,
    now: datetime,
) -> bool:
    """Apply an approve/reject/defer/escalate decision to a Nano."""
    stmt = select(Nano).where(Nano.id == case.content_id)
    result = await db.execute(stmt)
    nano = result.scalar_one_or_none()

    if not nano:
        # Content was deleted before the case was decided — nothing to update.
        return False

    if decision == "approve":
        # Validate that the Nano has all required metadata before publishing.
        _validate_nano_publishable(nano)
        nano.status = NanoStatus.PUBLISHED
        if nano.published_at is None:
            nano.published_at = now

    elif decision == "reject":
        nano.status = NanoStatus.DRAFT

    # defer / escalate: leave nano in pending_review; no status change.
    await db.flush()
    return decision in {"approve", "reject"}


def _validate_nano_publishable(nano: Nano) -> None:
    """Raise a 422 error if a Nano lacks the metadata required for publication.

    Mirrors the ``_validate_metadata_completeness`` check in the nanos service
    so that the moderation decision endpoint enforces the same invariant.
    """
    missing_fields: list[str] = []

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
            detail=(
                "Cannot publish: missing required metadata fields: " + ", ".join(missing_fields)
            ),
        )


async def _apply_rating_decision(
    *,
    db: AsyncSession,
    case: ModerationCase,
    decided_by: TokenData,
    request: ModerationReviewRequest,
    now: datetime,
) -> None:
    """Apply an approve/reject/defer/escalate decision to a NanoRating."""
    stmt = select(NanoRating).where(NanoRating.id == case.content_id)
    result = await db.execute(stmt)
    rating = result.scalar_one_or_none()

    if not rating:
        return

    decision = request.decision
    if decision == "approve":
        rating.moderation_status = FeedbackModerationStatus.APPROVED
        rating.moderated_at = now
        rating.moderated_by_user_id = decided_by.user_id
        rating.moderation_reason = request.reason
        await db.flush()
        # Sync denormalised rating cache on the parent Nano
        await _sync_nano_rating_cache(db=db, nano_id=rating.nano_id)

    elif decision == "reject":
        rating.moderation_status = FeedbackModerationStatus.HIDDEN
        rating.moderated_at = now
        rating.moderated_by_user_id = decided_by.user_id
        rating.moderation_reason = request.reason
        await db.flush()
        # Sync denormalised rating cache on the parent Nano
        await _sync_nano_rating_cache(db=db, nano_id=rating.nano_id)

    # defer / escalate: leave rating as PENDING, no moderation_status update.
    await db.flush()


async def _apply_comment_decision(
    *,
    db: AsyncSession,
    case: ModerationCase,
    decided_by: TokenData,
    request: ModerationReviewRequest,
    now: datetime,
) -> None:
    """Apply an approve/reject/defer/escalate decision to a NanoComment."""
    stmt = select(NanoComment).where(NanoComment.id == case.content_id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()

    if not comment:
        return

    decision = request.decision
    if decision == "approve":
        comment.moderation_status = FeedbackModerationStatus.APPROVED
        comment.moderated_at = now
        comment.moderated_by_user_id = decided_by.user_id
        comment.moderation_reason = request.reason

    elif decision == "reject":
        comment.moderation_status = FeedbackModerationStatus.HIDDEN
        comment.moderated_at = now
        comment.moderated_by_user_id = decided_by.user_id
        comment.moderation_reason = request.reason

    # defer / escalate: leave comment as PENDING.
    await db.flush()


async def _sync_nano_rating_cache(*, db: AsyncSession, nano_id: UUID) -> None:
    """Recompute and persist the denormalised average_rating / rating_count on Nano.

    This is a local reimplementation to avoid a cross-module import cycle with
    ``app.modules.nanos.service``.  The query is identical to the one in that
    module.
    """
    stmt = select(Nano).where(Nano.id == nano_id)
    result = await db.execute(stmt)
    nano = result.scalar_one_or_none()
    if not nano:
        return

    agg_stmt = select(
        func.count(NanoRating.id),
        func.avg(NanoRating.score),
    ).where(
        NanoRating.nano_id == nano_id,
        NanoRating.moderation_status == FeedbackModerationStatus.APPROVED,
    )
    agg_result = await db.execute(agg_stmt)
    rating_count_raw, average_raw = agg_result.one()

    rating_count = int(rating_count_raw)
    if rating_count == 0:
        nano.average_rating = Decimal("0.00")
        nano.rating_count = 0
    else:
        nano.average_rating = Decimal(str(average_raw)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        nano.rating_count = rating_count

    await db.flush()


# ---------------------------------------------------------------------------
# Content-detail enrichment
# ---------------------------------------------------------------------------


async def _get_content_detail(
    db: AsyncSession,
    content_type: ModerationContentType,
    content_id: UUID,
) -> Optional[NanoContentDetail | RatingContentDetail | CommentContentDetail]:
    """Load a type-specific content detail object for a queue item.

    Returns ``None`` if the underlying content record no longer exists.
    """
    if content_type == ModerationContentType.NANO:
        stmt = (
            select(Nano, User.username)
            .outerjoin(User, Nano.creator_id == User.id)
            .where(Nano.id == content_id)
        )
        row = (await db.execute(stmt)).first()
        if not row:
            return None
        nano, creator_username = row
        return NanoContentDetail(
            title=nano.title,
            creator_username=creator_username,
            status=nano.status.value,
            description=nano.description,
            uploaded_at=nano.uploaded_at,
        )

    if content_type == ModerationContentType.NANO_RATING:
        stmt = (
            select(NanoRating, User.username)
            .outerjoin(User, NanoRating.user_id == User.id)
            .where(NanoRating.id == content_id)
        )
        row = (await db.execute(stmt)).first()
        if not row:
            return None
        rating, username = row
        return RatingContentDetail(
            nano_id=rating.nano_id,
            score=rating.score,
            author_username=username,
            moderation_status=rating.moderation_status.value,
            created_at=rating.created_at,
        )

    if content_type == ModerationContentType.NANO_COMMENT:
        stmt = (
            select(NanoComment, User.username)
            .outerjoin(User, NanoComment.user_id == User.id)
            .where(NanoComment.id == content_id)
        )
        row = (await db.execute(stmt)).first()
        if not row:
            return None
        comment, username = row
        return CommentContentDetail(
            nano_id=comment.nano_id,
            content=comment.content,
            author_username=username,
            moderation_status=comment.moderation_status.value,
            created_at=comment.created_at,
        )

    return None


async def _load_content_details_for_cases(
    db: AsyncSession,
    cases: list[ModerationCase],
) -> dict[tuple[ModerationContentType, UUID], Optional[ContentDetail]]:
    """Batch-load content details for a queue page to avoid N+1 queries."""
    detail_map: dict[tuple[ModerationContentType, UUID], Optional[ContentDetail]] = {}

    if not cases:
        return detail_map

    nano_ids = [
        case.content_id for case in cases if case.content_type == ModerationContentType.NANO
    ]
    rating_ids = [
        case.content_id for case in cases if case.content_type == ModerationContentType.NANO_RATING
    ]
    comment_ids = [
        case.content_id for case in cases if case.content_type == ModerationContentType.NANO_COMMENT
    ]

    if nano_ids:
        rows = (
            await db.execute(
                select(Nano, User.username)
                .outerjoin(User, Nano.creator_id == User.id)
                .where(Nano.id.in_(nano_ids))
            )
        ).all()
        for nano, creator_username in rows:
            detail_map[(ModerationContentType.NANO, nano.id)] = NanoContentDetail(
                title=nano.title,
                creator_username=creator_username,
                status=nano.status.value,
                description=nano.description,
                uploaded_at=nano.uploaded_at,
            )

    if rating_ids:
        rows = (
            await db.execute(
                select(NanoRating, User.username)
                .outerjoin(User, NanoRating.user_id == User.id)
                .where(NanoRating.id.in_(rating_ids))
            )
        ).all()
        for rating, username in rows:
            detail_map[(ModerationContentType.NANO_RATING, rating.id)] = RatingContentDetail(
                nano_id=rating.nano_id,
                score=rating.score,
                author_username=username,
                moderation_status=rating.moderation_status.value,
                created_at=rating.created_at,
            )

    if comment_ids:
        rows = (
            await db.execute(
                select(NanoComment, User.username)
                .outerjoin(User, NanoComment.user_id == User.id)
                .where(NanoComment.id.in_(comment_ids))
            )
        ).all()
        for comment, username in rows:
            detail_map[(ModerationContentType.NANO_COMMENT, comment.id)] = CommentContentDetail(
                nano_id=comment.nano_id,
                content=comment.content,
                author_username=username,
                moderation_status=comment.moderation_status.value,
                created_at=comment.created_at,
            )

    for case in cases:
        detail_map.setdefault((case.content_type, case.content_id), None)

    return detail_map
