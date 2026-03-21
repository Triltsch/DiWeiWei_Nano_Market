"""
Tests for the Nano moderation workflow.

This module covers:
- GET /api/v1/nanos/pending-moderation  (moderator queue endpoint)
- PATCH /api/v1/nanos/{nano_id}/status  (moderator approve / reject transitions)

Scope:
- Access control: only MODERATOR and ADMIN may use the moderation queue endpoint
- Moderator can approve a pending_review Nano → published
- Moderator can reject (send back) a pending_review Nano → draft
- Moderator cannot act on Nanos that are not in pending_review status
- Regular users / creators cannot access the queue or perform moderator transitions
- Pagination of the moderation queue works correctly
"""

import uuid
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import (
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoFormat,
    NanoStatus,
    User,
    UserRole,
    UserStatus,
)
from app.modules.auth.service import verify_user_email

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def moderator_user(async_client, db_session) -> User:
    """
    Create, verify, and promote a user to MODERATOR role.

    Returns the User ORM instance after committing the role change.
    """
    data = {
        "email": f"moderator_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"moderator_{uuid.uuid4().hex[:8]}",
        "password": "ModeratorPass123!",
        "accept_terms": True,
        "accept_privacy": True,
    }

    resp = await async_client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 201
    user_id = UUID(resp.json()["id"])

    await verify_user_email(db_session, user_id)

    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one()
    user.role = UserRole.MODERATOR
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def moderator_token(async_client, moderator_user: User) -> str:
    """Return a valid JWT access token for the moderator user."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": moderator_user.email, "password": "ModeratorPass123!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _make_pending_nano(creator_id: UUID, title: str = "Pending Nano") -> Nano:
    """Factory helper that returns a fully populated *pending_review* Nano."""
    return Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        description="A complete description suitable for review.",
        duration_minutes=30,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="en",
        format=NanoFormat.VIDEO,
        status=NanoStatus.PENDING_REVIEW,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )


def _make_draft_nano(creator_id: UUID, title: str = "Draft Nano") -> Nano:
    """Factory helper that returns a fully populated *draft* Nano."""
    return Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        description="A draft description.",
        duration_minutes=20,
        competency_level=CompetencyLevel.BASIC,
        language="de",
        format=NanoFormat.TEXT,
        status=NanoStatus.DRAFT,
        version="1.0.0",
        license=LicenseType.CC_BY_SA,
    )


# ---------------------------------------------------------------------------
# Queue access control
# ---------------------------------------------------------------------------


class TestModerationQueueAccess:
    """
    Tests that the GET /pending-moderation endpoint enforces role-based access.

    Only MODERATOR and ADMIN roles should receive a 200 response.
    Unauthenticated requests and regular creator/consumer roles must be rejected.
    """

    @pytest.mark.asyncio
    async def test_moderator_can_access_queue(
        self, async_client, db_session, moderator_user, moderator_token
    ):
        """
        A user with MODERATOR role receives 200 and a valid response body.

        Validates:
        - Status code 200
        - Response contains 'nanos' list and 'pagination' object
        """
        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "nanos" in data
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_admin_can_access_queue(self, async_client, db_session, admin_token):
        """
        A user with ADMIN role receives 200 and a valid response body.

        Validates:
        - Status code 200
        - Response contains 'nanos' list and 'pagination' object
        """
        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "nanos" in data

    @pytest.mark.asyncio
    async def test_creator_cannot_access_queue(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        A user with CREATOR role (default after registration) is forbidden.

        Validates: 403 Forbidden response.
        """
        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_queue(self, async_client):
        """
        Requests without a JWT token must receive 401 Unauthorized.

        Validates: 401 response with no queue data leaked.
        """
        response = await async_client.get("/api/v1/nanos/pending-moderation")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Queue content
# ---------------------------------------------------------------------------


class TestModerationQueueContent:
    """
    Tests that the moderation queue returns the correct Nanos.

    Only Nanos in PENDING_REVIEW status should appear.
    Draft, published, archived, and deleted Nanos must be excluded.
    """

    @pytest.mark.asyncio
    async def test_queue_contains_pending_review_nanos(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        Nanos in pending_review status appear in the moderation queue.

        Validates:
        - Queue is non-empty after inserting a pending_review Nano
        - Returned item has correct nano_id, title, and status field
        """
        nano = _make_pending_nano(verified_user_id, title="Queued Nano")
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )
        assert response.status_code == 200
        nano_ids = [n["nano_id"] for n in response.json()["nanos"]]
        assert str(nano.id) in nano_ids

    @pytest.mark.asyncio
    async def test_queue_excludes_draft_nanos(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        Nanos that are still in draft status must not appear in the queue.

        Validates: Draft Nano's ID is absent from the nanos list.
        """
        draft = _make_draft_nano(verified_user_id, title="Invisible Draft")
        db_session.add(draft)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )
        assert response.status_code == 200
        nano_ids = [n["nano_id"] for n in response.json()["nanos"]]
        assert str(draft.id) not in nano_ids

    @pytest.mark.asyncio
    async def test_queue_is_empty_when_no_pending_nanos(
        self, async_client, db_session, moderator_token
    ):
        """
        When no Nanos are in pending_review status the queue is empty.

        Validates:
        - 200 response
        - 'nanos' list is empty
        - 'pagination' total_items is 0
        """
        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nanos"] == []
        assert data["pagination"]["total_results"] == 0

    @pytest.mark.asyncio
    async def test_queue_item_includes_creator_username(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        Each queue item must include creator_username for moderator context.

        Validates: 'creator_username' field is present and non-empty.
        """
        nano = _make_pending_nano(verified_user_id, title="Creator Username Test")
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/nanos/pending-moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )
        assert response.status_code == 200
        nanos = response.json()["nanos"]
        matching = [n for n in nanos if n["nano_id"] == str(nano.id)]
        assert len(matching) == 1
        assert matching[0]["creator_username"]


# ---------------------------------------------------------------------------
# Moderator approve (pending_review → published)
# ---------------------------------------------------------------------------


class TestModeratorApprove:
    """
    Tests for moderator approving a Nano (pending_review → published).
    """

    @pytest.mark.asyncio
    async def test_moderator_can_approve_pending_review_nano(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        A moderator can transition a pending_review Nano to published.

        Validates:
        - 200 response
        - old_status = 'pending_review', new_status = 'published'
        - published_at is set in the database
        """
        nano = _make_pending_nano(verified_user_id)
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "published", "reason": "Looks good, approved."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "pending_review"
        assert data["new_status"] == "published"
        assert data["published_at"] is not None

        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PUBLISHED
        assert nano.published_at is not None

    @pytest.mark.asyncio
    async def test_admin_can_approve_pending_review_nano(
        self, async_client, db_session, verified_user_id, admin_token
    ):
        """
        An admin user can also approve Nanos (same as moderator privilege).

        Validates: 200 with new_status = 'published'.
        """
        nano = _make_pending_nano(verified_user_id, title="Admin Approve Test")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "published"},
        )

        assert response.status_code == 200
        assert response.json()["new_status"] == "published"

    @pytest.mark.asyncio
    async def test_moderator_cannot_approve_draft_nano(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        A moderator may only act on Nanos in pending_review status.
        Attempting to approve a draft Nano must be rejected.

        Validates: 403 Forbidden response.
        """
        draft = _make_draft_nano(verified_user_id, title="Cannot Approve Draft")
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        response = await async_client.patch(
            f"/api/v1/nanos/{draft.id}/status",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "published"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_creator_cannot_directly_publish(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        A regular creator is not allowed to publish their own pending_review Nano.
        The publish decision belongs to moderators only.

        Validates: 403 Forbidden response.
        """
        nano = _make_pending_nano(verified_user_id, title="Creator Cannot Publish")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "published"},
        )

        # Creator may not approve their own pending_review Nano
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Moderator reject (pending_review → draft)
# ---------------------------------------------------------------------------


class TestModeratorReject:
    """
    Tests for moderator rejecting a Nano and sending it back to draft.
    """

    @pytest.mark.asyncio
    async def test_moderator_can_reject_pending_review_nano(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        A moderator can reject a pending_review Nano, returning it to draft.

        Validates:
        - 200 response
        - old_status = 'pending_review', new_status = 'draft'
        - Database status is reset to DRAFT
        """
        nano = _make_pending_nano(verified_user_id, title="To Be Rejected")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "draft", "reason": "Needs more detail in description."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "pending_review"
        assert data["new_status"] == "draft"

        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_moderator_cannot_reject_already_published_nano(
        self, async_client, db_session, verified_user_id, moderator_token
    ):
        """
        A moderator may only act on pending_review Nanos.
        Attempting to reject a published Nano must be refused.

        Validates: 403 Forbidden response.
        """
        from datetime import datetime, timezone

        published_nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Already Published",
            description="Published and cannot be rejected by moderator.",
            duration_minutes=25,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            published_at=datetime.now(timezone.utc),
        )
        db_session.add(published_nano)
        await db_session.commit()
        await db_session.refresh(published_nano)

        response = await async_client.patch(
            f"/api/v1/nanos/{published_nano.id}/status",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "draft"},
        )

        assert response.status_code == 403
