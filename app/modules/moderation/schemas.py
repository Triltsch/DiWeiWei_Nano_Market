"""
Pydantic schemas for the Moderation Queue API.

This module defines the request and response models for the content review
workflow endpoints introduced in Sprint 8, Story 6.2.

Design goals:
- Unified queue item schema that works for all content types (nano, rating, comment).
- A ``content_detail`` field carries type-specific details as a typed discriminated
  union, allowing clients to introspect the reviewable content without extra lookups.
- ``reporter_id`` is present but nullable, reserved for user-submitted flags from
  Story 6.3.  Clients should treat a null value as "system-initiated review".
"""

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import ModerationCaseStatus, ModerationContentType


class ModerationDecision(str):
    """Allowed decision values for a moderation review action.

    Kept as a plain string constant enum for backwards-compatible OpenAPI
    representation and to avoid a circular-import on the model enum.
    """

    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    ESCALATE = "escalate"


VALID_DECISIONS: frozenset[str] = frozenset({"approve", "reject", "defer", "escalate"})


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ModerationReviewRequest(BaseModel):
    """
    Request body for submitting a moderation decision.

    Attributes:
        decision:       Required action: approve | reject | defer | escalate.
        reason:         Human-readable explanation for the decision (max 500 chars).
                        Recommended for all decisions; required semantically for
                        reject, defer, and escalate.
        deferred_until: Target re-review date for DEFERRED decisions.  Ignored
                        for other decision types.
    """

    decision: Annotated[str, Field(description="approve | reject | defer | escalate")]
    reason: Optional[Annotated[str, Field(max_length=500)]] = None
    deferred_until: Optional[datetime] = None

    def is_valid_decision(self) -> bool:
        """Return True if decision is one of the recognised values."""
        return self.decision in VALID_DECISIONS


# ---------------------------------------------------------------------------
# Content-detail sub-schemas (type-specific enrichment in queue items)
# ---------------------------------------------------------------------------


class NanoContentDetail(BaseModel):
    """Content detail for a Nano under review."""

    title: str
    creator_username: Optional[str] = None
    status: str
    description: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class RatingContentDetail(BaseModel):
    """Content detail for a user rating under review."""

    nano_id: UUID
    score: int
    author_username: Optional[str] = None
    moderation_status: str
    created_at: Optional[datetime] = None


class CommentContentDetail(BaseModel):
    """Content detail for a user comment under review."""

    nano_id: UUID
    content: str
    author_username: Optional[str] = None
    moderation_status: str
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Queue response schemas
# ---------------------------------------------------------------------------


class ModerationQueueItem(BaseModel):
    """A single entry in the moderation review queue.

    ``content_detail`` contains type-specific information about the reviewable
    content.  Its structure depends on ``content_type``:
    - ``nano``         → :class:`NanoContentDetail`
    - ``nano_rating``  → :class:`RatingContentDetail`
    - ``nano_comment`` → :class:`CommentContentDetail`

    The field is ``None`` if the underlying content record can no longer be
    found (orphaned case after a deletion race condition).
    """

    case_id: UUID
    content_type: ModerationContentType
    content_id: UUID
    reporter_id: Optional[UUID] = None  # reserved for Story 6.3 flags
    status: ModerationCaseStatus
    reason: Optional[str] = None
    decided_by_user_id: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    deferred_until: Optional[datetime] = None
    escalation_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    content_detail: Optional[Any] = None


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    current_page: int
    page_size: int
    total_results: int
    total_pages: int
    has_next_page: bool
    has_prev_page: bool


class ModerationQueueResponse(BaseModel):
    """Paginated list of moderation review cases."""

    items: list[ModerationQueueItem]
    pagination: PaginationMeta
