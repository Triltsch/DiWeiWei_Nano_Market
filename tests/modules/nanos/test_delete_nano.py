"""
Tests for the DELETE /api/v1/nanos/{nano_id} endpoint.

This module covers:
- Successful soft-deletion of a DRAFT Nano by its creator
- Successful soft-deletion of an ARCHIVED Nano by its creator
- Rejection of deletion when Nano is PUBLISHED
- Rejection of deletion when Nano is in PENDING_REVIEW status
- 403 when a different creator tries to delete another creator's Nano
- 401 when an unauthenticated request is made
- 404 when Nano does not exist

Each test verifies the HTTP status code and, where applicable, the state of
the database record after the request.
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
# Helper factories
# ---------------------------------------------------------------------------


def _make_nano(creator_id: UUID, status: NanoStatus, title: str = "Test Nano") -> Nano:
    """
    Create a minimally valid Nano with the given status.

    All required fields are populated so that the ORM does not raise
    constraint errors.
    """
    return Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        description="A description sufficient for testing.",
        duration_minutes=20,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="en",
        format=NanoFormat.TEXT,
        status=status,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def second_creator(async_client, db_session) -> User:
    """
    Register, verify, and return a second creator user.

    Used to verify that deleting another user's Nano is forbidden.
    """
    data = {
        "email": f"creator2_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"creator2_{uuid.uuid4().hex[:8]}",
        "password": "Creator2Pass123!",
        "accept_terms": True,
        "accept_privacy": True,
    }
    resp = await async_client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 201
    user_id = UUID(resp.json()["id"])

    await verify_user_email(db_session, user_id)

    result = await db_session.execute(select(User).where(User.id == user_id))
    return result.scalar_one()


@pytest.fixture
async def second_creator_token(async_client, second_creator: User) -> str:
    """Return a JWT access token for the second creator user."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": second_creator.email, "password": "Creator2Pass123!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Success cases
# ---------------------------------------------------------------------------


class TestDeleteNanoSuccess:
    """
    Tests that confirm a creator can delete Nanos in valid states.

    A successful deletion soft-deletes the Nano (status → DELETED) and
    returns HTTP 200 with a NanoDeleteResponse body.
    """

    @pytest.mark.asyncio
    async def test_creator_can_delete_draft_nano(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        A creator can delete their own DRAFT Nano.

        Validates:
        - 200 response
        - Response body contains nano_id, status='deleted', and a message
        - Database record status is set to DELETED
        """
        nano = _make_nano(verified_user_id, NanoStatus.DRAFT, "Delete Draft Test")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.delete(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["nano_id"] == str(nano.id)
        assert body["status"] == "deleted"
        assert body["message"]

        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DELETED

    @pytest.mark.asyncio
    async def test_creator_can_delete_archived_nano(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        A creator can delete their own ARCHIVED Nano.

        Archived Nanos (unpublished from the marketplace) can be fully deleted
        by the owner without first changing status again.

        Validates:
        - 200 response
        - Database record status is set to DELETED
        """
        nano = _make_nano(verified_user_id, NanoStatus.ARCHIVED, "Delete Archived Test")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.delete(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DELETED


# ---------------------------------------------------------------------------
# Business rule violations
# ---------------------------------------------------------------------------


class TestDeleteNanoBusinessRules:
    """
    Tests that rejection rules are enforced when the Nano is not in a
    deletable state.

    Only DRAFT and ARCHIVED Nanos can be deleted.
    """

    @pytest.mark.asyncio
    async def test_cannot_delete_published_nano(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Published Nanos must be archived before they can be deleted.

        The business rule prevents removing live content without the explicit
        archival step, which revokes public visibility first.

        Validates: 400 Bad Request response.
        """
        from datetime import datetime, timezone

        nano = _make_nano(verified_user_id, NanoStatus.PUBLISHED, "Live Nano")
        nano.published_at = datetime.now(timezone.utc)
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.delete(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400

        # Verify the Nano was NOT deleted
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_cannot_delete_pending_review_nano(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Nanos awaiting moderation review cannot be deleted directly.

        A creator must first withdraw the Nano from review (→ draft) before
        deletion is permitted. This prevents orphaned review queue entries.

        Validates: 400 Bad Request response.
        """
        nano = _make_nano(verified_user_id, NanoStatus.PENDING_REVIEW, "Under Review Nano")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.delete(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400

        # Verify the Nano was NOT deleted
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PENDING_REVIEW


# ---------------------------------------------------------------------------
# Authorization violations
# ---------------------------------------------------------------------------


class TestDeleteNanoAuthorization:
    """
    Tests that ensure only the owning creator can delete a Nano.
    """

    @pytest.mark.asyncio
    async def test_cannot_delete_another_creators_nano(
        self,
        async_client,
        db_session,
        verified_user_id,
        second_creator: User,
        second_creator_token: str,
    ):
        """
        Creator A cannot delete a Nano owned by Creator B.

        Validates: 403 Forbidden response regardless of the Nano state.
        """
        # Nano owned by the first creator (verified_user_id)
        nano = _make_nano(verified_user_id, NanoStatus.DRAFT, "Protected Nano")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Request from the second creator
        response = await async_client.delete(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {second_creator_token}"},
        )

        assert response.status_code == 403

        # Original Nano must be unchanged
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_delete_nano(
        self, async_client, db_session, verified_user_id
    ):
        """
        Unauthenticated requests to DELETE /nanos/{id} must be rejected with 401.

        Validates: 401 Unauthorized response when no JWT is provided.
        """
        nano = _make_nano(verified_user_id, NanoStatus.DRAFT, "Auth Guard Test")
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        response = await async_client.delete(f"/api/v1/nanos/{nano.id}")

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Not Found
# ---------------------------------------------------------------------------


class TestDeleteNanoNotFound:
    """Tests for deletion requests targeting non-existent Nanos."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_nano_returns_404(self, async_client, access_token):
        """
        Deleting a Nano that does not exist must return 404 Not Found.

        Validates: 404 response with informative error detail.
        """
        random_id = uuid.uuid4()

        response = await async_client.delete(
            f"/api/v1/nanos/{random_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404
