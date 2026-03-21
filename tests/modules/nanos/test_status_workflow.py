"""
Tests for Nano status workflow endpoint.

This module tests the PATCH /api/v1/nanos/{nano_id}/status endpoint
including state machine validation, authorization, metadata completeness,
and audit logging.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoFormat,
    NanoStatus,
    User,
    UserRole,
    UserStatus,
)


class TestUpdateNanoStatus:
    """
    Test suite for PATCH /api/v1/nanos/{nano_id}/status endpoint.

    Tests status workflow transitions including state machine validation,
    authorization, metadata completeness checks, and audit logging.
    """

    @pytest.mark.asyncio
    async def test_update_status_pending_review_to_published_success(
        self, async_client, db_session, verified_user_id, admin_user, admin_token
    ):
        """
        Test successful moderator/admin approval from pending_review to published.

        Validates:
        - Transition is allowed
        - published_at timestamp is set
        - Audit log entry is created
        """
        # Create a complete Nano in pending_review status
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Complete Nano",
            description="This is a complete nano ready for publishing",
            duration_minutes=45,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Moderator/admin approves and publishes the Nano
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "published", "reason": "Ready for public release"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nano_id"] == str(nano.id)
        assert data["old_status"] == "pending_review"
        assert data["new_status"] == "published"
        assert data["published_at"] is not None
        assert data["archived_at"] is None

        # Verify database was updated
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PUBLISHED
        assert nano.published_at is not None

        # Verify audit log entry was created
        stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == "nano")
            .where(AuditLog.resource_id == str(nano.id))
            .where(AuditLog.action == AuditAction.DATA_MODIFIED)
        )
        result = await db_session.execute(stmt)
        audit_entry = result.scalar_one_or_none()

        assert audit_entry is not None
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.event_data["field"] == "status"
        assert audit_entry.event_data["old_value"] == "pending_review"
        assert audit_entry.event_data["new_value"] == "published"
        assert audit_entry.event_data["reason"] == "Ready for public release"

    @pytest.mark.asyncio
    async def test_update_status_published_to_archived_success(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Test successful status transition from published to archived.

        Validates:
        - Transition is allowed
        - archived_at timestamp is set
        """
        # Create a published Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Nano",
            description="This nano is already published",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY_SA,
            published_at=datetime.now(timezone.utc) - timedelta(days=7),
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Update status to archived
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "archived"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "published"
        assert data["new_status"] == "archived"
        assert data["archived_at"] is not None

        # Verify database was updated
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.ARCHIVED
        assert nano.archived_at is not None

    @pytest.mark.asyncio
    async def test_update_status_published_to_draft_within_24h(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Test successful unpublish within 24 hours of publication.

        Business rule: Published Nanos can be reverted to draft within 24h.
        """
        # Create a recently published Nano (1 hour ago)
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Recently Published Nano",
            description="Published just 1 hour ago",
            duration_minutes=15,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.QUIZ,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC0,
            published_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Update status back to draft
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "draft"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "published"
        assert data["new_status"] == "draft"

        # Verify database was updated
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DRAFT

    @pytest.mark.asyncio
    async def test_update_status_published_to_draft_after_24h_fails(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Test that unpublishing fails after 24 hours.

        Business rule: Cannot revert to draft after 24h, must archive instead.
        """
        # Create a Nano published more than 24 hours ago
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Old Published Nano",
            description="Published 2 days ago",
            duration_minutes=60,
            competency_level=CompetencyLevel.ADVANCED,
            language="en",
            format=NanoFormat.INTERACTIVE,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.PROPRIETARY,
            published_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to update status back to draft (should fail)
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "draft"},
        )

        assert response.status_code == 400
        assert "24 hours" in response.json()["detail"]
        assert "archived" in response.json()["detail"].lower()

        # Verify status was not changed
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition_fails(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Test that invalid status transitions are rejected.

        Example: deleted → draft is not allowed.
        """
        # Create a deleted Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Deleted Nano",
            description="This nano is deleted",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.DELETED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to restore a deleted Nano to draft (should fail)
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "draft"},
        )

        assert response.status_code == 400
        assert "invalid status transition" in response.json()["detail"].lower()

        # Verify status was not changed
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DELETED

    @pytest.mark.asyncio
    async def test_update_status_requires_complete_metadata_for_publishing(
        self, async_client, db_session, verified_user_id, admin_token
    ):
        """
        Test that publishing requires complete metadata.

        pending_review → published transition validates:
        - title (non-empty)
        - description (non-empty)
        - duration_minutes (> 0)
        - language (present)
        """
        # Create an incomplete Nano already submitted for review (missing description)
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Incomplete Nano",
            description="",  # Empty description
            duration_minutes=None,  # Missing duration
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to publish without complete metadata (should fail)
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "published"},
        )

        assert response.status_code == 400
        assert "metadata" in response.json()["detail"].lower()
        assert "description" in response.json()["detail"]
        assert "duration_minutes" in response.json()["detail"]

        # Verify status was not changed
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_update_status_requires_authentication(self, async_client, db_session):
        """Test that status update requires authentication."""
        # Create user and Nano
        user = User(
            id=uuid.uuid4(),
            email="testuser@example.com",
            username="testuser",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=user.id,
            title="Test Nano",
            description="Test description",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to update status without authentication
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            json={"status": "published"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_status_requires_creator_authorization(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """Test that only the creator can update Nano status."""
        # Create a different user who is not the creator
        other_user = User(
            id=uuid.uuid4(),
            email="otheruser@example.com",
            username="otheruser",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create a Nano owned by the other user
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=other_user.id,
            title="Other User's Nano",
            description="This nano belongs to another user",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to update status as verified_user (not the creator)
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "published"},
        )

        assert response.status_code == 403
        assert "creator" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, async_client, verified_user_id, access_token):
        """Test that updating non-existent Nano returns 404."""
        non_existent_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/nanos/{non_existent_id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "published"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_status_noop_when_already_target(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """
        Test that updating to the same status is a no-op.

        Should return success but not modify anything.
        """
        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Draft Nano",
            description="Already in draft status",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Update status to draft (already draft)
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "draft"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "draft"
        assert data["new_status"] == "draft"

    @pytest.mark.asyncio
    async def test_update_status_invalid_status_value(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """Test that invalid status values are rejected."""
        # Create a Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
            description="Test",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Try to update with invalid status value
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "invalid_status"},
        )

        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_update_status_draft_to_pending_review(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """Test transition from draft to pending_review."""
        # Create a complete Nano in draft status
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Ready for Review",
            description="This nano is ready for review",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY_SA,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Update status to pending_review
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "pending_review"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "draft"
        assert data["new_status"] == "pending_review"

        # Verify database was updated
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_update_status_archived_to_deleted(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """Test transition from archived to deleted."""
        # Create an archived Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Archived Nano",
            description="This nano is archived",
            duration_minutes=25,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.MIXED,
            status=NanoStatus.ARCHIVED,
            version="1.0.0",
            license=LicenseType.PROPRIETARY,
            archived_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Update status to deleted
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": "deleted"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["old_status"] == "archived"
        assert data["new_status"] == "deleted"

        # Verify database was updated
        await db_session.refresh(nano)
        assert nano.status == NanoStatus.DELETED
