"""
Router for the Moderation Queue API (Sprint 8 — Story 6.2).

Exposes three endpoints under ``/api/v1/moderation``:

- ``GET  /queue``                  — Paginated, filterable moderation queue
- ``GET  /queue/{case_id}``        — Single case detail
- ``POST /cases/{case_id}/review`` — Submit a moderation decision

All endpoints require the caller to hold the ``moderator`` or ``admin`` role.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModerationCaseStatus, ModerationContentType
from app.modules.auth.middleware import (
    ROLE_ADMIN,
    ROLE_MODERATOR,
    require_any_role,
)
from app.modules.auth.tokens import TokenData
from app.modules.moderation.schemas import (
    ModerationQueueItem,
    ModerationQueueResponse,
    ModerationReviewRequest,
)
from app.modules.moderation.service import (
    get_moderation_case,
    get_moderation_queue,
    review_moderation_case,
)


def get_moderation_router(
    prefix: str = "/api/v1/moderation", tags: list[str] | None = None
) -> APIRouter:
    """Create and configure the moderation router.

    Args:
        prefix: URL prefix for all moderation endpoints.
        tags:   OpenAPI tags for documentation grouping.

    Returns:
        Configured :class:`fastapi.APIRouter` instance.
    """
    if tags is None:
        tags = ["Moderation"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(
        "/queue",
        response_model=ModerationQueueResponse,
        status_code=status.HTTP_200_OK,
        summary="Get moderation queue",
        description="""
        Retrieve the paginated moderation review queue.

        **Access control:** ``moderator`` or ``admin`` role required.

        **Query Parameters:**
        - ``content_type``: Filter by content type (``nano``, ``nano_rating``, ``nano_comment``).
          Returns all types when omitted.
        - ``status``: Filter by case status (default: ``pending``).  Pass ``all`` to include
          every status.
        - ``page``: 1-indexed page number (default: 1).
        - ``limit``: Results per page (1–100, default: 20).

        **Response:** Paginated list of :class:`ModerationQueueItem` objects enriched
        with type-specific ``content_detail``.
        """,
    )
    async def queue(
        current_user: Annotated[TokenData, Depends(require_any_role(ROLE_MODERATOR, ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
        content_type: Annotated[
            ModerationContentType | None,
            Query(description="Filter by content type (nano, nano_rating, nano_comment)"),
        ] = None,
        case_status: Annotated[
            str,
            Query(
                alias="status",
                description="Filter by case status. Use 'all' to include every status.",
            ),
        ] = "pending",
        page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Results per page (1–100)")] = 20,
    ) -> ModerationQueueResponse:
        # Map "all" to None so the service includes all statuses.
        resolved_status: ModerationCaseStatus | None
        if case_status == "all":
            resolved_status = None
        else:
            try:
                resolved_status = ModerationCaseStatus(case_status)
            except ValueError:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Invalid status '{case_status}'.  "
                        "Allowed values: pending, approved, rejected, deferred, escalated, all."
                    ),
                )

        return await get_moderation_queue(
            db=db,
            content_type=content_type,
            status_filter=resolved_status,
            page=page,
            limit=limit,
        )

    @router.get(
        "/queue/{case_id}",
        response_model=ModerationQueueItem,
        status_code=status.HTTP_200_OK,
        summary="Get a single moderation case",
        description="""
        Retrieve a single moderation case by its ID, enriched with content details.

        **Access control:** ``moderator`` or ``admin`` role required.
        """,
    )
    async def case_detail(
        case_id: UUID,
        current_user: Annotated[TokenData, Depends(require_any_role(ROLE_MODERATOR, ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> ModerationQueueItem:
        return await get_moderation_case(db=db, case_id=case_id)

    @router.post(
        "/cases/{case_id}/review",
        response_model=ModerationQueueItem,
        status_code=status.HTTP_200_OK,
        summary="Submit a moderation decision",
        description="""
        Apply a moderation decision to a case and update the underlying content.

        **Access control:** ``moderator`` or ``admin`` role required.

        **Decision semantics:**

        | Decision  | Nano effect             | Rating / Comment effect |
        |-----------|-------------------------|-------------------------|
        | approve   | → ``published``         | → ``approved``          |
        | reject    | → ``draft``             | → ``hidden``            |
        | defer     | stays ``pending_review``| stays ``pending``       |
        | escalate  | stays ``pending_review``| stays ``pending``       |

        For ``defer`` you may supply ``deferred_until`` to indicate when the case
        should be revisited.  For ``escalate``, the ``reason`` field is copied into
        ``escalation_note`` on the case.

        A granular audit-log entry (``moderation_approved``, ``moderation_rejected``,
        ``moderation_deferred``, or ``moderation_escalated``) is created atomically
        with the content update.
        """,
    )
    async def review(
        case_id: UUID,
        request: ModerationReviewRequest,
        current_user: Annotated[TokenData, Depends(require_any_role(ROLE_MODERATOR, ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> ModerationQueueItem:
        return await review_moderation_case(
            db=db,
            case_id=case_id,
            request=request,
            decided_by=current_user,
        )

    return router
