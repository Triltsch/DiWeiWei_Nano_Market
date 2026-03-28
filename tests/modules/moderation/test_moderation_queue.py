"""
Moderation Queue API tests (Sprint 8, Story 6.2).

Scope:
- Access control for moderation queue endpoints.
- Queue retrieval with filtering and pagination.
- Review decisions (approve, reject, defer, escalate) for nanos, ratings, comments.
- Audit-log creation for moderation decisions.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    CompetencyLevel,
    FeedbackModerationStatus,
    LicenseType,
    ModerationCase,
    ModerationCaseStatus,
    ModerationContentType,
    Nano,
    NanoComment,
    NanoFormat,
    NanoRating,
    NanoStatus,
    User,
    UserRole,
)
from app.modules.auth.service import verify_user_email


async def _create_user_with_role(async_client, db_session, role: UserRole, password: str) -> User:
    """Create a verified user and assign a role for role-gated endpoint tests."""
    payload = {
        "email": f"{role.value}_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"{role.value}_{uuid.uuid4().hex[:8]}",
        "password": password,
        "accept_terms": True,
        "accept_privacy": True,
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    user_id = UUID(response.json()["id"])
    await verify_user_email(db_session, user_id)

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.role = role
    await db_session.commit()
    await db_session.refresh(user)

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": password},
    )
    assert login.status_code == 200
    user.access_token = login.json()["access_token"]  # type: ignore[attr-defined]
    return user


def _make_nano(*, creator_id: UUID, status: NanoStatus, title: str) -> Nano:
    """Create a Nano model with required publication metadata."""
    return Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        description="Complete metadata for moderation flow tests.",
        duration_minutes=25,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="en",
        format=NanoFormat.VIDEO,
        status=status,
        version="1.0.0",
        license=LicenseType.CC_BY,
        file_storage_path="nanos/test-content.zip",
    )


@pytest.fixture
async def moderator_user(async_client, db_session) -> User:
    """Create a verified moderator user with an attached access token string."""
    return await _create_user_with_role(
        async_client=async_client,
        db_session=db_session,
        role=UserRole.MODERATOR,
        password="ModeratorPass123!",
    )


@pytest.fixture
async def moderator_token(moderator_user: User) -> str:
    """Return access token prepared in the moderator fixture."""
    return moderator_user.access_token  # type: ignore[attr-defined]


@pytest.fixture
async def creator_user(async_client, db_session) -> User:
    """Create a verified regular creator user for ownership-bound content records."""
    return await _create_user_with_role(
        async_client=async_client,
        db_session=db_session,
        role=UserRole.CREATOR,
        password="CreatorPass123!",
    )


@pytest.fixture
async def creator_token(creator_user: User) -> str:
    """Return access token prepared in the creator fixture."""
    return creator_user.access_token  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_queue_access_control(async_client, creator_token, moderator_token, admin_token):
    """Validate that moderation queue access is restricted to moderator/admin roles."""
    # Unauthenticated requests are rejected.
    unauth = await async_client.get("/api/v1/moderation/queue")
    assert unauth.status_code == 401

    # Creator role is forbidden.
    creator_resp = await async_client.get(
        "/api/v1/moderation/queue",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert creator_resp.status_code == 403

    # Moderator and admin roles are allowed.
    mod_resp = await async_client.get(
        "/api/v1/moderation/queue",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert mod_resp.status_code == 200

    admin_resp = await async_client.get(
        "/api/v1/moderation/queue",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200


@pytest.mark.asyncio
async def test_queue_filter_and_pagination(async_client, db_session, creator_user, moderator_token):
    """Validate queue filtering and paginated responses for moderation case listings."""
    nano = _make_nano(
        creator_id=creator_user.id, status=NanoStatus.PENDING_REVIEW, title="Queue Nano"
    )

    rating_nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PUBLISHED,
        title="Queue Rated Nano",
    )

    comment_nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PUBLISHED,
        title="Queue Comment Nano",
    )

    rating = NanoRating(
        id=uuid.uuid4(),
        nano_id=rating_nano.id,
        user_id=creator_user.id,
        score=5,
        moderation_status=FeedbackModerationStatus.PENDING,
    )

    comment = NanoComment(
        id=uuid.uuid4(),
        nano_id=comment_nano.id,
        user_id=creator_user.id,
        content="Pending comment for moderation queue tests.",
        moderation_status=FeedbackModerationStatus.PENDING,
    )

    db_session.add_all([nano, rating_nano, comment_nano, rating, comment])
    await db_session.flush()

    cases = [
        ModerationCase(content_type=ModerationContentType.NANO, content_id=nano.id),
        ModerationCase(content_type=ModerationContentType.NANO_RATING, content_id=rating.id),
        ModerationCase(content_type=ModerationContentType.NANO_COMMENT, content_id=comment.id),
    ]
    db_session.add_all(cases)
    await db_session.commit()

    # Type filter should only return rating cases.
    type_filtered = await async_client.get(
        "/api/v1/moderation/queue?content_type=nano_rating",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert type_filtered.status_code == 200
    payload = type_filtered.json()
    assert payload["pagination"]["total_results"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["content_type"] == "nano_rating"

    # Pagination should split 3 cases into pages of size 2.
    page_two = await async_client.get(
        "/api/v1/moderation/queue?page=2&limit=2&status=all",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert page_two.status_code == 200
    page_two_payload = page_two.json()
    assert page_two_payload["pagination"]["current_page"] == 2
    assert page_two_payload["pagination"]["page_size"] == 2
    assert page_two_payload["pagination"]["total_results"] == 3
    assert page_two_payload["pagination"]["total_pages"] == 2
    assert page_two_payload["pagination"]["has_prev_page"] is True
    assert page_two_payload["pagination"]["has_next_page"] is False
    assert len(page_two_payload["items"]) == 1


@pytest.mark.asyncio
async def test_review_approve_nano_publishes_and_writes_audit(
    async_client,
    db_session,
    creator_user,
    moderator_user,
    moderator_token,
):
    """Validate that approving a nano case publishes content and records an audit event."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PENDING_REVIEW,
        title="Approval Candidate",
    )
    db_session.add(nano)
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO,
        content_id=nano.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    review = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={"decision": "approve", "reason": "Meets publication standards."},
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert review.status_code == 200

    await db_session.refresh(nano)
    await db_session.refresh(case)

    assert nano.status == NanoStatus.PUBLISHED
    assert nano.published_at is not None
    assert case.status == ModerationCaseStatus.APPROVED
    assert case.decided_by_user_id == moderator_user.id

    log_stmt = select(AuditLog).where(
        AuditLog.action == AuditAction.MODERATION_APPROVED,
        AuditLog.resource_type == "nano",
        AuditLog.resource_id == str(nano.id),
    )
    log = (await db_session.execute(log_stmt)).scalar_one_or_none()
    assert log is not None


@pytest.mark.asyncio
async def test_review_reject_rating_hides_and_recalculates_cache(
    async_client,
    db_session,
    creator_user,
    moderator_token,
):
    """Validate rating rejection hides feedback and updates denormalized rating cache."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PUBLISHED,
        title="Rated Nano",
    )
    nano.average_rating = Decimal("4.50")
    nano.rating_count = 1

    rating = NanoRating(
        id=uuid.uuid4(),
        nano_id=nano.id,
        user_id=creator_user.id,
        score=4,
        moderation_status=FeedbackModerationStatus.APPROVED,
    )

    db_session.add_all([nano, rating])
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO_RATING,
        content_id=rating.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    review = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={"decision": "reject", "reason": "Manipulated rating signal."},
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert review.status_code == 200

    await db_session.refresh(rating)
    await db_session.refresh(nano)
    await db_session.refresh(case)

    assert rating.moderation_status == FeedbackModerationStatus.HIDDEN
    assert rating.moderated_at is not None
    assert rating.moderation_reason == "Manipulated rating signal."
    assert nano.rating_count == 0
    assert nano.average_rating == Decimal("0.00")
    assert case.status == ModerationCaseStatus.REJECTED


@pytest.mark.asyncio
async def test_review_approve_comment_sets_comment_moderation_fields(
    async_client,
    db_session,
    creator_user,
    moderator_user,
    moderator_token,
):
    """Validate comment approval updates moderation fields and case status."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PUBLISHED,
        title="Commented Nano",
    )

    comment = NanoComment(
        id=uuid.uuid4(),
        nano_id=nano.id,
        user_id=creator_user.id,
        content="Please review this pending comment.",
        moderation_status=FeedbackModerationStatus.PENDING,
    )

    db_session.add_all([nano, comment])
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO_COMMENT,
        content_id=comment.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    review = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={"decision": "approve", "reason": "Constructive and policy-compliant."},
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert review.status_code == 200

    await db_session.refresh(comment)
    await db_session.refresh(case)

    assert comment.moderation_status == FeedbackModerationStatus.APPROVED
    assert comment.moderated_by_user_id == moderator_user.id
    assert comment.moderated_at is not None
    assert case.status == ModerationCaseStatus.APPROVED


@pytest.mark.asyncio
async def test_review_defer_sets_case_deferral_without_changing_nano(
    async_client,
    db_session,
    creator_user,
    moderator_token,
):
    """Validate defer decision stores deferred date and keeps nano in pending review."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PENDING_REVIEW,
        title="Deferred Nano",
    )
    db_session.add(nano)
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO,
        content_id=nano.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    deferred_until = datetime.now(timezone.utc) + timedelta(days=3)
    review = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={
            "decision": "defer",
            "reason": "Waiting for policy team clarification.",
            "deferred_until": deferred_until.isoformat(),
        },
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert review.status_code == 200

    await db_session.refresh(nano)
    await db_session.refresh(case)

    assert nano.status == NanoStatus.PENDING_REVIEW
    assert case.status == ModerationCaseStatus.DEFERRED
    assert case.deferred_until is not None


@pytest.mark.asyncio
async def test_review_escalate_sets_case_note_without_changing_comment(
    async_client,
    db_session,
    creator_user,
    moderator_token,
):
    """Validate escalate decision stores escalation note and leaves comment pending."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PUBLISHED,
        title="Escalation Nano",
    )

    comment = NanoComment(
        id=uuid.uuid4(),
        nano_id=nano.id,
        user_id=creator_user.id,
        content="Potentially policy-sensitive content.",
        moderation_status=FeedbackModerationStatus.PENDING,
    )

    db_session.add_all([nano, comment])
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO_COMMENT,
        content_id=comment.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    review = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={"decision": "escalate", "reason": "Needs legal review."},
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert review.status_code == 200

    await db_session.refresh(comment)
    await db_session.refresh(case)

    assert comment.moderation_status == FeedbackModerationStatus.PENDING
    assert case.status == ModerationCaseStatus.ESCALATED
    assert case.escalation_note == "Needs legal review."


@pytest.mark.asyncio
async def test_review_invalid_decision_returns_422(
    async_client, db_session, creator_user, moderator_token
):
    """Validate invalid moderation decisions are rejected with 422 responses."""
    nano = _make_nano(
        creator_id=creator_user.id,
        status=NanoStatus.PENDING_REVIEW,
        title="Invalid Decision Nano",
    )
    db_session.add(nano)
    await db_session.flush()

    case = ModerationCase(
        content_type=ModerationContentType.NANO,
        content_id=nano.id,
        status=ModerationCaseStatus.PENDING,
    )
    db_session.add(case)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/moderation/cases/{case.id}/review",
        json={"decision": "banish", "reason": "Not a valid action."},
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert response.status_code == 422
    assert "Invalid decision" in response.json()["detail"]
