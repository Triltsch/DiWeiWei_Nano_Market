"""
Tests for Nano metadata API routes.

This module tests the metadata endpoints including GET and POST operations
with proper authentication and authorization checks.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    Category,
    CompetencyLevel,
    FeedbackModerationStatus,
    LicenseType,
    Nano,
    NanoCategoryAssignment,
    NanoComment,
    NanoFormat,
    NanoRating,
    NanoStatus,
)
from app.modules.auth.tokens import create_access_token
from app.modules.upload.storage import StorageError


class TestGetNanoMetadata:
    """
    Test suite for GET /api/v1/nanos/{nano_id} endpoint.

    Tests retrieving Nano metadata including authentication,
    authorization, and various metadata states.
    """

    @pytest.mark.asyncio
    async def test_get_nano_metadata_success(self, async_client, db_session):
        """Test successfully retrieving Nano metadata."""
        # Create a user
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email="creator@example.com",
            username="creator",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()

        # Create a Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=user.id,
            title="Test Nano",
            description="A test learning module",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()
        await db_session.refresh(nano)

        # Retrieve Nano metadata
        response = await async_client.get(f"/api/v1/nanos/{nano.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["nano_id"] == str(nano.id)
        assert data["title"] == "Test Nano"
        assert data["description"] == "A test learning module"
        assert data["duration_minutes"] == 30
        assert data["competency_level"] == "beginner"
        assert data["language"] == "de"
        assert data["format"] == "video"
        assert data["status"] == "published"
        assert data["license"] == "CC-BY"

    @pytest.mark.asyncio
    async def test_get_nano_metadata_non_published_requires_authentication(
        self, async_client, db_session
    ):
        """Non-published Nano metadata requires authentication."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email="creator3@example.com",
            username="creator3",
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
            title="Restricted Nano",
            description="Restricted metadata",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_nano_metadata_non_published_admin_allowed(
        self, async_client, db_session, verified_user_id
    ):
        """Admin role can access non-published metadata."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Draft Nano For Admin",
            description="Admin-visible metadata",
            duration_minutes=30,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="en",
            format=NanoFormat.MIXED,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC0,
        )
        db_session.add(nano)
        await db_session.commit()

        admin_token, _ = create_access_token(uuid.uuid4(), "admin@example.com", role="admin")
        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nano_id"] == str(nano.id)

    @pytest.mark.asyncio
    async def test_get_nano_metadata_not_found(self, async_client):
        """Test retrieving non-existent Nano returns 404."""
        non_existent_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/nanos/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_nano_metadata_with_categories(self, async_client, db_session):
        """Test retrieving Nano metadata with categories."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email="creator2@example.com",
            username="creator2",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()

        # Create categories
        cat1 = Category(
            id=uuid.uuid4(),
            name="Programming",
            description="Programming courses",
            status="active",
        )
        cat2 = Category(
            id=uuid.uuid4(),
            name="Python",
            description="Python courses",
            parent_category_id=cat1.id,
            status="active",
        )
        db_session.add(cat1)
        db_session.add(cat2)
        await db_session.flush()

        # Create Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=user.id,
            title="Python Basics",
            description="Learn Python",
            duration_minutes=45,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY_SA,
        )
        db_session.add(nano)
        await db_session.flush()

        # Assign categories
        assignment1 = NanoCategoryAssignment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            category_id=cat1.id,
            rank=0,
        )
        assignment2 = NanoCategoryAssignment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            category_id=cat2.id,
            rank=1,
        )
        db_session.add(assignment1)
        db_session.add(assignment2)
        await db_session.commit()

        # Retrieve metadata
        response = await async_client.get(f"/api/v1/nanos/{nano.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["categories"]) == 2
        assert data["categories"][0]["name"] == "Programming"
        assert data["categories"][1]["name"] == "Python"


class TestCreatorNanoListRoute:
    """Test suite for GET /api/v1/nanos/my-nanos route behavior."""

    @pytest.mark.asyncio
    async def test_get_my_nanos_route_not_shadowed_by_nano_id(self, async_client, db_session):
        """Static /my-nanos route resolves correctly and does not produce UUID 422 errors."""
        from app.models import User, UserRole, UserStatus

        creator = User(
            id=uuid.uuid4(),
            email="creator-list@example.com",
            username="creator_list",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="en",
            login_attempts=0,
        )
        db_session.add(creator)
        await db_session.flush()

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="My Draft Nano",
            description="Editable content",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.MIXED,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.PROPRIETARY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(creator.id, creator.email, role="creator")
        response = await async_client.get(
            "/api/v1/nanos/my-nanos",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "nanos" in data
        assert isinstance(data["nanos"], list)
        assert data["nanos"][0]["title"] == "My Draft Nano"


class TestUpdateNanoMetadata:
    """
    Test suite for POST /api/v1/nanos/{nano_id}/metadata endpoint.

    Tests updating Nano metadata with validation, authentication,
    and authorization checks.
    """

    @pytest.mark.asyncio
    async def test_update_nano_metadata_success(self, async_client, verified_user_id, db_session):
        """Test successfully updating Nano metadata."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create a Nano owned by the test user
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Original Title",
            description="Original description",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.MIXED,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.PROPRIETARY,
        )
        db_session.add(nano)
        await db_session.commit()

        # Update metadata
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Updated Title",
                "description": "Updated description with more details",
                "duration_minutes": 45,
                "competency_level": "intermediate",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nano_id"] == str(nano.id)
        assert data["status"] == "draft"
        assert "title" in data["updated_fields"]
        assert "description" in data["updated_fields"]
        assert "duration_minutes" in data["updated_fields"]
        assert "competency_level" in data["updated_fields"]

        # Verify changes were persisted
        get_response = await async_client.get(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        updated_data = get_response.json()
        assert updated_data["title"] == "Updated Title"
        assert updated_data["description"] == "Updated description with more details"
        assert updated_data["duration_minutes"] == 45
        assert updated_data["competency_level"] == "intermediate"

    @pytest.mark.asyncio
    async def test_update_nano_metadata_requires_authentication(self, async_client, db_session):
        """Test that updating metadata requires authentication."""
        # Create a Nano
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email="owner@example.com",
            username="owner",
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

        # Try to update without authentication
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            json={"title": "Unauthorized Update"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_nano_metadata_requires_creator(
        self, async_client, verified_user_id, db_session
    ):
        """Test that only the creator can update metadata."""
        # Create another user
        from app.models import User, UserRole, UserStatus

        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            username="other",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create Nano owned by other_user
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=other_user.id,
            title="Other's Nano",
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

        # Get token for verified_user (not the creator)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Try to update as non-creator
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Unauthorized Update"},
        )

        assert response.status_code == 403
        assert "creator" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nano_metadata_only_draft(
        self, async_client, verified_user_id, db_session
    ):
        """Test that only draft Nanos can be updated."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create a published Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Nano",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,  # Not DRAFT
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        # Try to update published Nano
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Attempt to Update Published"},
        )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nano_metadata_validation(
        self, async_client, verified_user_id, db_session
    ):
        """Test metadata validation rules."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
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

        # Test title too long
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "A" * 201},  # Max 200
        )
        assert response.status_code == 422

        # Test description too long
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "B" * 2001},  # Max 2000
        )
        assert response.status_code == 422

        # Test invalid competency level
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"competency_level": "expert"},  # Not valid
        )
        assert response.status_code == 422

        # Test invalid format
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"format": "audio"},  # Not valid
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_nano_metadata_requires_fields(
        self, async_client, verified_user_id, db_session
    ):
        """Test that at least one field must be provided."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
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

        # Try to update with empty payload
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 400
        assert "at least one field" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nano_metadata_with_categories(
        self, async_client, verified_user_id, db_session
    ):
        """Test updating Nano with category assignments."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create categories
        cat1 = Category(
            id=uuid.uuid4(),
            name="Science",
            description="Science courses",
            status="active",
        )
        cat2 = Category(
            id=uuid.uuid4(),
            name="Math",
            description="Math courses",
            status="active",
        )
        db_session.add(cat1)
        db_session.add(cat2)
        await db_session.flush()

        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
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

        # Update with categories
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_ids": [str(cat1.id), str(cat2.id)]},
        )

        assert response.status_code == 200
        assert "categories" in response.json()["updated_fields"]

        # Verify categories were assigned
        get_response = await async_client.get(
            f"/api/v1/nanos/{nano.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data["categories"]) == 2

    @pytest.mark.asyncio
    async def test_update_nano_metadata_invalid_category(
        self, async_client, verified_user_id, db_session
    ):
        """Test that invalid category IDs are rejected."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
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

        # Try to update with non-existent category
        fake_category_id = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_ids": [str(fake_category_id)]},
        )

        assert response.status_code == 400
        assert "category" in response.json()["detail"].lower()
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nano_metadata_max_categories(
        self, async_client, verified_user_id, db_session
    ):
        """Test that maximum 5 categories can be assigned."""
        # Get authentication token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create 6 categories
        category_ids = []
        for i in range(6):
            cat = Category(
                id=uuid.uuid4(),
                name=f"Category {i}",
                description=f"Description {i}",
                status="active",
            )
            db_session.add(cat)
            category_ids.append(cat.id)
        await db_session.flush()

        # Create a draft Nano
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Test Nano",
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

        # Try to assign 6 categories (should fail, max is 5)
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/metadata",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_ids": [str(cid) for cid in category_ids]},
        )

        assert response.status_code == 422
        assert "5" in response.text or "maximum" in response.text.lower()


class TestNanoDetailViewRoutes:
    """
    Test suite for Nano detail view and download info endpoints.

    Covers public/restricted visibility rules and download access control.
    """

    @pytest.mark.asyncio
    async def test_get_nano_detail_published_is_public(
        self, async_client, db_session, verified_user_id
    ):
        """Published Nano details are visible without authentication."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Public Nano",
            description="Publicly visible nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/public-nano.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}/detail")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["nano_id"] == str(nano.id)
        assert payload["data"]["title"] == "Public Nano"
        assert payload["meta"]["visibility"] == "public"
        assert payload["data"]["download_info"]["requires_authentication"] is True
        assert payload["data"]["download_info"]["can_download"] is False
        assert payload["data"]["download_info"]["download_path"] is None
        assert payload["timestamp"]

    @pytest.mark.asyncio
    async def test_get_nano_detail_non_published_requires_authentication(
        self, async_client, db_session, verified_user_id
    ):
        """Non-published Nano details require authentication."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Draft Nano",
            description="Not public",
            duration_minutes=30,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/draft-nano.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}/detail")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_nano_detail_non_published_forbidden_for_other_user(
        self, async_client, db_session, verified_user_id
    ):
        """Authenticated non-owner without elevated role cannot access non-published Nano."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Private Nano",
            description="Restricted detail view",
            duration_minutes=25,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.MIXED,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC0,
            file_storage_path="nanos/private-nano.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        other_token, _ = create_access_token(uuid.uuid4(), "other@example.com", role="consumer")

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/detail",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nano_detail_non_published_owner_allowed(
        self, async_client, db_session, verified_user_id, access_token
    ):
        """Creator can access non-published Nano detail view."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Owner Draft Nano",
            description="Owner visible",
            duration_minutes=35,
            competency_level=CompetencyLevel.ADVANCED,
            language="de",
            format=NanoFormat.QUIZ,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.PROPRIETARY,
            file_storage_path="nanos/owner-draft.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/detail",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["visibility"] == "restricted"
        assert payload["data"]["download_info"]["can_download"] is True
        assert payload["data"]["download_info"]["download_path"] == "nanos/owner-draft.zip"

    @pytest.mark.asyncio
    async def test_get_nano_detail_non_published_admin_allowed(
        self, async_client, db_session, verified_user_id
    ):
        """Admin role can access non-published Nano detail view."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Admin View Nano",
            description="Restricted but admin-visible",
            duration_minutes=22,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/admin-view.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        admin_token, _ = create_access_token(uuid.uuid4(), "admin@example.com", role="admin")
        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/detail",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["download_info"]["can_download"] is True
        assert payload["data"]["download_info"]["download_path"] == "nanos/admin-view.zip"

    @pytest.mark.asyncio
    async def test_download_info_requires_authentication(
        self, async_client, db_session, verified_user_id
    ):
        """Download info endpoint requires authentication, even for published Nano."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Public Download Nano",
            duration_minutes=10,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/public-download.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}/download-info")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_info_non_published_forbidden_for_other_user(
        self, async_client, db_session, verified_user_id
    ):
        """Download path for non-published Nano is blocked for unauthorized authenticated users."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Restricted Download Nano",
            duration_minutes=15,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.INTERACTIVE,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC_BY_SA,
            file_storage_path="nanos/restricted-download.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        other_token, _ = create_access_token(uuid.uuid4(), "other@example.com", role="consumer")

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download-info",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_download_info_published_authenticated_success(
        self, async_client, db_session, verified_user_id, access_token, monkeypatch
    ):
        """Authenticated users can resolve a presigned download URL for published Nanos."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Download Nano",
            duration_minutes=40,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/published-download.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        storage_adapter = Mock()
        storage_adapter.get_file_url.return_value = (
            "https://minio.local/published-download.zip?signature=test"
        )
        monkeypatch.setattr(
            "app.modules.nanos.service.get_storage_adapter", lambda: storage_adapter
        )

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download-info",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["nano_id"] == str(nano.id)
        assert payload["data"]["can_download"] is True
        assert (
            payload["data"]["download_url"]
            == "https://minio.local/published-download.zip?signature=test"
        )
        assert payload["meta"]["visibility"] == "public"
        storage_adapter.get_file_url.assert_called_once_with(
            object_key="nanos/published-download.zip"
        )

    @pytest.mark.asyncio
    async def test_download_info_non_published_moderator_allowed(
        self, async_client, db_session, verified_user_id, monkeypatch
    ):
        """Moderator role can resolve a presigned download URL for non-published Nano."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Moderator Download Nano",
            duration_minutes=50,
            competency_level=CompetencyLevel.ADVANCED,
            language="en",
            format=NanoFormat.INTERACTIVE,
            status=NanoStatus.PENDING_REVIEW,
            version="1.0.0",
            license=LicenseType.CC_BY_SA,
            file_storage_path="nanos/moderator-download.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        moderator_token, _ = create_access_token(
            uuid.uuid4(),
            "moderator@example.com",
            role="moderator",
        )

        storage_adapter = Mock()
        storage_adapter.get_file_url.return_value = (
            "https://minio.local/moderator-download.zip?signature=test"
        )
        monkeypatch.setattr(
            "app.modules.nanos.service.get_storage_adapter", lambda: storage_adapter
        )

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download-info",
            headers={"Authorization": f"Bearer {moderator_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["can_download"] is True
        assert (
            payload["data"]["download_url"]
            == "https://minio.local/moderator-download.zip?signature=test"
        )
        assert payload["meta"]["visibility"] == "restricted"
        storage_adapter.get_file_url.assert_called_once_with(
            object_key="nanos/moderator-download.zip"
        )

    @pytest.mark.asyncio
    async def test_download_info_returns_503_when_storage_unavailable(
        self, async_client, db_session, verified_user_id, access_token, monkeypatch
    ):
        """Download info endpoint returns 503 when presigned URL generation fails."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Download Failure Nano",
            duration_minutes=25,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/published-download-failure.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        storage_adapter = Mock()
        storage_adapter.get_file_url.side_effect = StorageError("presign failed")
        monkeypatch.setattr(
            "app.modules.nanos.service.get_storage_adapter", lambda: storage_adapter
        )

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download-info",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "Download URL is temporarily unavailable"

    @pytest.mark.asyncio
    async def test_download_redirect_requires_authentication(
        self, async_client, db_session, verified_user_id
    ):
        """Direct download endpoint requires authentication."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Public Redirect Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/public-redirect.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}/download")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_redirect_returns_307_with_presigned_url(
        self, async_client, db_session, verified_user_id, access_token, monkeypatch
    ):
        """Direct download endpoint returns redirect to storage URL for authorized caller."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Redirect Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/published-redirect.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        storage_adapter = Mock()
        storage_adapter.get_file_url.return_value = "https://minio.local/signed-download-url"
        monkeypatch.setattr(
            "app.modules.nanos.service.get_storage_adapter", lambda: storage_adapter
        )

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download",
            headers={"Authorization": f"Bearer {access_token}"},
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert response.headers["location"] == "https://minio.local/signed-download-url"
        storage_adapter.get_file_url.assert_called_once_with(
            object_key="nanos/published-redirect.zip",
        )

    @pytest.mark.asyncio
    async def test_download_redirect_returns_503_when_storage_unavailable(
        self, async_client, db_session, verified_user_id, access_token, monkeypatch
    ):
        """Direct download endpoint returns 503 when presigned URL generation fails."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=verified_user_id,
            title="Published Redirect Failure Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
            file_storage_path="nanos/published-redirect-failure.zip",
        )
        db_session.add(nano)
        await db_session.commit()

        storage_adapter = Mock()
        storage_adapter.get_file_url.side_effect = StorageError("presign failed")
        monkeypatch.setattr(
            "app.modules.nanos.service.get_storage_adapter", lambda: storage_adapter
        )

        response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/download",
            headers={"Authorization": f"Bearer {access_token}"},
            follow_redirects=False,
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "Download URL is temporarily unavailable"


class TestNanoRatingsRoutes:
    """Test suite for Nano star-rating routes."""

    @staticmethod
    async def _create_user(db_session, email: str, username: str):
        """Create and persist a user for rating tests."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="en",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.mark.asyncio
    async def test_create_rating_success_and_cache_update(self, async_client, db_session):
        """Creating a rating succeeds but remains pending until moderation approves it."""
        creator = await self._create_user(
            db_session, "creator-rating@example.com", "creator_rating"
        )
        rater = await self._create_user(db_session, "rater1@example.com", "rater1")

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Published Rated Nano",
            duration_minutes=15,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(rater.id, rater.email, role="creator")
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 5},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["nano_id"] == str(nano.id)
        assert payload["user_rating"]["score"] == 5
        assert payload["user_rating"]["moderation_status"] == "pending"
        assert Decimal(str(payload["aggregation"]["average_rating"])) == Decimal("0.00")
        assert Decimal(str(payload["aggregation"]["median_rating"])) == Decimal("0.00")
        assert payload["aggregation"]["rating_count"] == 0
        assert payload["aggregation"]["distribution"] == [
            {"score": 1, "count": 0},
            {"score": 2, "count": 0},
            {"score": 3, "count": 0},
            {"score": 4, "count": 0},
            {"score": 5, "count": 0},
        ]

        await db_session.refresh(nano)
        assert nano.average_rating == Decimal("0.00")
        assert nano.rating_count == 0

    @pytest.mark.asyncio
    async def test_create_rating_requires_authentication(self, async_client, db_session):
        """Creating a rating requires authentication."""
        creator = await self._create_user(db_session, "creator-auth@example.com", "creator_auth")
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Published Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            json={"score": 4},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_rating_only_for_published_nanos(self, async_client, db_session):
        """Creating a rating for non-published Nano returns 400."""
        creator = await self._create_user(db_session, "creator-draft@example.com", "creator_draft")
        rater = await self._create_user(db_session, "rater-draft@example.com", "rater_draft")
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Draft Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(rater.id, rater.email, role="creator")
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 3},
        )

        assert response.status_code == 400
        assert "published" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_rating_duplicate_returns_409(self, async_client, db_session):
        """Creating a second rating for same user/nano returns 409 conflict."""
        creator = await self._create_user(db_session, "creator-dup@example.com", "creator_dup")
        rater = await self._create_user(db_session, "rater-dup@example.com", "rater_dup")
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Conflict Nano",
            duration_minutes=30,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.MIXED,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(rater.id, rater.email, role="creator")
        first_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 2},
        )
        second_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 4},
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert "already exists" in second_response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_rating_success_and_aggregation_consistent(self, async_client, db_session):
        """Updating own rating resets moderation and removes it from public aggregation."""
        creator = await self._create_user(
            db_session, "creator-update@example.com", "creator_update"
        )
        rater_1 = await self._create_user(db_session, "rater-update1@example.com", "rater_update1")
        rater_2 = await self._create_user(db_session, "rater-update2@example.com", "rater_update2")

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Aggregation Nano",
            duration_minutes=25,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="en",
            format=NanoFormat.INTERACTIVE,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()

        db_session.add(
            NanoRating(
                id=uuid.uuid4(),
                nano_id=nano.id,
                user_id=rater_1.id,
                score=4,
                moderation_status=FeedbackModerationStatus.APPROVED,
            )
        )
        db_session.add(
            NanoRating(
                id=uuid.uuid4(),
                nano_id=nano.id,
                user_id=rater_2.id,
                score=2,
                moderation_status=FeedbackModerationStatus.APPROVED,
            )
        )
        await db_session.commit()

        token, _ = create_access_token(rater_2.id, rater_2.email, role="creator")
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/ratings/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 5},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["user_rating"]["score"] == 5
        assert payload["user_rating"]["moderation_status"] == "pending"
        assert Decimal(str(payload["aggregation"]["average_rating"])) == Decimal("4.00")
        assert Decimal(str(payload["aggregation"]["median_rating"])) == Decimal("4.00")
        assert payload["aggregation"]["rating_count"] == 1
        assert payload["aggregation"]["distribution"] == [
            {"score": 1, "count": 0},
            {"score": 2, "count": 0},
            {"score": 3, "count": 0},
            {"score": 4, "count": 1},
            {"score": 5, "count": 0},
        ]

        await db_session.refresh(nano)
        assert nano.average_rating == Decimal("4.00")
        assert nano.rating_count == 1

    @pytest.mark.asyncio
    async def test_update_rating_without_existing_rating_returns_404(
        self, async_client, db_session
    ):
        """Updating a non-existing own rating returns 404."""
        creator = await self._create_user(
            db_session, "creator-missing@example.com", "creator_missing"
        )
        rater = await self._create_user(db_session, "rater-missing@example.com", "rater_missing")
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="No Existing Rating Nano",
            duration_minutes=12,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(rater.id, rater.email, role="creator")
        response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/ratings/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 3},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rating_summary_public_and_authenticated_user_rating(
        self, async_client, db_session
    ):
        """Read endpoint is public but aggregates only approved ratings."""
        creator = await self._create_user(db_session, "creator-read@example.com", "creator_read")
        rater_1 = await self._create_user(db_session, "rater-read1@example.com", "rater_read1")
        rater_2 = await self._create_user(db_session, "rater-read2@example.com", "rater_read2")

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Read Rating Nano",
            duration_minutes=18,
            competency_level=CompetencyLevel.ADVANCED,
            language="de",
            format=NanoFormat.QUIZ,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()

        db_session.add(
            NanoRating(
                id=uuid.uuid4(),
                nano_id=nano.id,
                user_id=rater_1.id,
                score=1,
                moderation_status=FeedbackModerationStatus.APPROVED,
            )
        )
        db_session.add(
            NanoRating(
                id=uuid.uuid4(),
                nano_id=nano.id,
                user_id=rater_2.id,
                score=5,
                moderation_status=FeedbackModerationStatus.PENDING,
            )
        )
        await db_session.commit()

        public_response = await async_client.get(f"/api/v1/nanos/{nano.id}/ratings")
        assert public_response.status_code == 200
        public_payload = public_response.json()
        assert public_payload["current_user_rating"] is None
        assert Decimal(str(public_payload["aggregation"]["average_rating"])) == Decimal("1.00")
        assert Decimal(str(public_payload["aggregation"]["median_rating"])) == Decimal("1.00")
        assert public_payload["aggregation"]["rating_count"] == 1

        token, _ = create_access_token(rater_2.id, rater_2.email, role="creator")
        auth_response = await async_client.get(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert auth_response.status_code == 200
        auth_payload = auth_response.json()
        assert auth_payload["current_user_rating"] is not None
        assert auth_payload["current_user_rating"]["score"] == 5
        assert auth_payload["current_user_rating"]["moderation_status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_rating_summary_non_published_returns_400(self, async_client, db_session):
        """Read endpoint returns 400 when Nano is not published."""
        creator = await self._create_user(
            db_session, "creator-read-draft@example.com", "creator_read_draft"
        )
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Draft Rating Nano",
            duration_minutes=22,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/nanos/{nano.id}/ratings")

        assert response.status_code == 400
        assert "published" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_rating_score_validation_returns_422(self, async_client, db_session):
        """Score outside 1-5 range is rejected by request schema validation."""
        creator = await self._create_user(
            db_session, "creator-validation@example.com", "creator_validation"
        )
        rater = await self._create_user(
            db_session, "rater-validation@example.com", "rater_validation"
        )
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Validation Nano",
            duration_minutes=14,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(rater.id, rater.email, role="creator")
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/ratings",
            headers={"Authorization": f"Bearer {token}"},
            json={"score": 6},
        )

        assert response.status_code == 422


class TestNanoCommentsRoutes:
    """Test suite for Nano comments/reviews routes."""

    @staticmethod
    async def _create_user(db_session, email: str, username: str):
        """Create and persist a user for comment tests."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="en",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.mark.asyncio
    async def test_create_comment_success_with_sanitization(self, async_client, db_session):
        """Valid comment is created pending moderation and sanitized before persistence."""
        creator = await self._create_user(
            db_session, "comment-creator@example.com", "comment_creator"
        )
        commenter = await self._create_user(db_session, "comment-user@example.com", "comment_user")

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Commentable Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(commenter.id, commenter.email, role="creator")
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "  <script>alert('x')</script> Great nano!  "},
        )

        assert response.status_code == 201
        payload = response.json()["comment"]
        assert payload["nano_id"] == str(nano.id)
        assert payload["user_id"] == str(commenter.id)
        assert payload["content"] == "&lt;script&gt;alert('x')&lt;/script&gt; Great nano!"
        assert payload["moderation_status"] == "pending"
        assert payload["is_edited"] is False

    @pytest.mark.asyncio
    async def test_create_comment_rejects_blank_and_duplicate(self, async_client, db_session):
        """Blank comments are rejected and duplicate comment per user/nano returns 409."""
        creator = await self._create_user(
            db_session, "comment-creator2@example.com", "comment_creator2"
        )
        commenter = await self._create_user(
            db_session, "comment-user2@example.com", "comment_user2"
        )
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Duplicate Guard Nano",
            duration_minutes=15,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(commenter.id, commenter.email, role="creator")
        blank_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "   "},
        )
        assert blank_response.status_code == 422

        first_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "First review"},
        )
        second_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Second review"},
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_comment_rejects_post_sanitization_overflow(
        self, async_client, db_session
    ):
        """Content that exceeds max length after HTML escaping is rejected with 422."""
        creator = await self._create_user(
            db_session, "comment-creator-overflow@example.com", "comment_creator_overflow"
        )
        commenter = await self._create_user(
            db_session, "comment-user-overflow@example.com", "comment_user_overflow"
        )
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Sanitization Overflow Nano",
            duration_minutes=10,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(commenter.id, commenter.email, role="creator")
        response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "<" * 1000},
        )

        assert response.status_code == 422
        assert "exceeds maximum length" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_comments_only_allowed_for_published_nanos(self, async_client, db_session):
        """Listing and creating comments for non-published Nanos returns 400."""
        creator = await self._create_user(
            db_session, "comment-creator3@example.com", "comment_creator3"
        )
        commenter = await self._create_user(
            db_session, "comment-user3@example.com", "comment_user3"
        )
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Draft Comment Nano",
            duration_minutes=15,
            competency_level=CompetencyLevel.INTERMEDIATE,
            language="de",
            format=NanoFormat.VIDEO,
            status=NanoStatus.DRAFT,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        token, _ = create_access_token(commenter.id, commenter.email, role="creator")
        list_response = await async_client.get(f"/api/v1/nanos/{nano.id}/comments")
        create_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Should fail"},
        )

        assert list_response.status_code == 400
        assert create_response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_comments_pagination_and_stable_sort(self, async_client, db_session):
        """Comments list shows only approved comments, stably sorted by updated_at and id."""
        creator = await self._create_user(
            db_session, "comment-creator4@example.com", "comment_creator4"
        )
        user_a = await self._create_user(db_session, "comment-a@example.com", "comment_a")
        user_b = await self._create_user(db_session, "comment-b@example.com", "comment_b")
        user_c = await self._create_user(db_session, "comment-c@example.com", "comment_c")

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Pagination Nano",
            duration_minutes=25,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.MIXED,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()

        base = datetime.now(timezone.utc)
        c1 = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=user_a.id,
            content="oldest",
            moderation_status=FeedbackModerationStatus.APPROVED,
            created_at=base - timedelta(minutes=3),
            updated_at=base - timedelta(minutes=3),
        )
        c2 = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=user_b.id,
            content="middle",
            moderation_status=FeedbackModerationStatus.HIDDEN,
            created_at=base - timedelta(minutes=2),
            updated_at=base - timedelta(minutes=2),
        )
        c3 = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=user_c.id,
            content="newest",
            moderation_status=FeedbackModerationStatus.APPROVED,
            created_at=base - timedelta(minutes=1),
            updated_at=base - timedelta(minutes=1),
        )
        db_session.add_all([c1, c2, c3])
        await db_session.commit()

        page_1 = await async_client.get(f"/api/v1/nanos/{nano.id}/comments?page=1&limit=2")
        page_2 = await async_client.get(f"/api/v1/nanos/{nano.id}/comments?page=2&limit=2")

        assert page_1.status_code == 200
        assert page_2.status_code == 200

        page_1_payload = page_1.json()
        assert [item["content"] for item in page_1_payload["comments"]] == ["newest", "oldest"]
        assert page_1_payload["pagination"]["total_results"] == 2
        assert page_1_payload["pagination"]["has_next_page"] is False

        page_2_payload = page_2.json()
        assert page_2_payload["comments"] == []
        assert page_2_payload["pagination"]["has_prev_page"] is True

    @pytest.mark.asyncio
    async def test_update_comment_owner_and_admin_permissions(self, async_client, db_session):
        """Owner can edit own comment, non-owner gets 403, admin edit re-queues moderation."""
        from app.models import UserRole

        creator = await self._create_user(
            db_session, "comment-creator5@example.com", "comment_creator5"
        )
        owner = await self._create_user(db_session, "comment-owner@example.com", "comment_owner")
        outsider = await self._create_user(
            db_session, "comment-outsider@example.com", "comment_outsider"
        )
        admin = await self._create_user(db_session, "comment-admin@example.com", "comment_admin")
        admin.role = UserRole.ADMIN

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="RBAC Nano",
            duration_minutes=30,
            competency_level=CompetencyLevel.ADVANCED,
            language="en",
            format=NanoFormat.QUIZ,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()

        comment = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=owner.id,
            content="Original comment",
            moderation_status=FeedbackModerationStatus.APPROVED,
        )
        db_session.add(comment)
        await db_session.commit()

        owner_token, _ = create_access_token(owner.id, owner.email, role="creator")
        outsider_token, _ = create_access_token(outsider.id, outsider.email, role="creator")
        admin_token, _ = create_access_token(admin.id, admin.email, role="admin")

        owner_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"content": "Owner update"},
        )
        forbidden_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={"content": "Outsider update"},
        )
        admin_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"content": "<b>Admin moderated</b>"},
        )

        assert owner_response.status_code == 200
        assert forbidden_response.status_code == 403
        assert admin_response.status_code == 200
        assert admin_response.json()["comment"]["content"] == "&lt;b&gt;Admin moderated&lt;/b&gt;"
        assert admin_response.json()["comment"]["moderation_status"] == "pending"

    @pytest.mark.asyncio
    async def test_moderation_endpoints_control_public_feedback_visibility(
        self, async_client, db_session
    ):
        """Moderator decisions change what public rating and comment endpoints expose."""
        from app.models import User, UserRole, UserStatus

        creator = await self._create_user(
            db_session, "feedback-mod-creator@example.com", "feedback_mod_creator"
        )
        author = await self._create_user(
            db_session, "feedback-mod-author@example.com", "feedback_mod_author"
        )
        moderator = User(
            id=uuid.uuid4(),
            email="feedback-mod-moderator@example.com",
            username="feedback_mod_moderator",
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.MODERATOR,
            preferred_language="en",
            login_attempts=0,
        )
        db_session.add(moderator)

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Moderated Feedback Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()

        rating = NanoRating(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=author.id,
            score=5,
            moderation_status=FeedbackModerationStatus.PENDING,
        )
        comment = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=author.id,
            content="Needs review",
            moderation_status=FeedbackModerationStatus.PENDING,
        )
        db_session.add_all([rating, comment])
        await db_session.commit()

        moderator_token, _ = create_access_token(moderator.id, moderator.email, role="moderator")

        public_before = await async_client.get(f"/api/v1/nanos/{nano.id}/ratings")
        comments_before = await async_client.get(f"/api/v1/nanos/{nano.id}/comments")
        assert public_before.status_code == 200
        assert public_before.json()["aggregation"]["rating_count"] == 0
        assert comments_before.status_code == 200
        assert comments_before.json()["comments"] == []

        approve_rating = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/ratings/{rating.id}/moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "approved", "reason": "Legitimate review"},
        )
        approve_comment = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}/moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "approved", "reason": "Looks fine"},
        )

        assert approve_rating.status_code == 200
        assert approve_rating.json()["rating"]["moderation_status"] == "approved"
        assert approve_comment.status_code == 200
        assert approve_comment.json()["comment"]["moderation_status"] == "approved"

        public_after_approve = await async_client.get(f"/api/v1/nanos/{nano.id}/ratings")
        comments_after_approve = await async_client.get(f"/api/v1/nanos/{nano.id}/comments")
        assert public_after_approve.json()["aggregation"]["rating_count"] == 1
        assert comments_after_approve.json()["comments"][0]["content"] == "Needs review"
        assert "moderation_reason" not in comments_after_approve.json()["comments"][0]

        hide_comment = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}/moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "hidden", "reason": "Policy violation"},
        )
        assert hide_comment.status_code == 200
        assert hide_comment.json()["comment"]["moderation_status"] == "hidden"

        comments_after_hide = await async_client.get(f"/api/v1/nanos/{nano.id}/comments")
        assert comments_after_hide.json()["comments"] == []

        rating_log_stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == "nano_rating")
            .where(AuditLog.resource_id == str(rating.id))
            .where(AuditLog.action == AuditAction.DATA_MODIFIED)
        )
        rating_log = (await db_session.execute(rating_log_stmt)).scalar_one_or_none()
        assert rating_log is not None
        assert rating_log.event_data["old_value"] == "pending"
        assert rating_log.event_data["new_value"] == "approved"

        comment_log_stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == "nano_comment")
            .where(AuditLog.resource_id == str(comment.id))
            .where(AuditLog.action == AuditAction.DATA_MODIFIED)
            .where(AuditLog.event_data["new_value"].as_string() == "hidden")
        )
        comment_log = (await db_session.execute(comment_log_stmt)).scalar_one_or_none()
        assert comment_log is not None
        assert comment_log.event_data["old_value"] == "approved"
        assert comment_log.event_data["new_value"] == "hidden"

    @pytest.mark.asyncio
    async def test_feedback_moderation_requires_moderator_or_admin(self, async_client, db_session):
        """Regular creators cannot moderate feedback items."""
        creator = await self._create_user(
            db_session, "feedback-rbac-creator@example.com", "feedback_rbac_creator"
        )
        author = await self._create_user(
            db_session, "feedback-rbac-author@example.com", "feedback_rbac_author"
        )

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Feedback RBAC Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        rating = NanoRating(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=author.id,
            score=3,
            moderation_status=FeedbackModerationStatus.PENDING,
        )
        comment = NanoComment(
            id=uuid.uuid4(),
            nano_id=nano.id,
            user_id=author.id,
            content="Review awaiting moderation",
            moderation_status=FeedbackModerationStatus.PENDING,
        )
        db_session.add_all([nano, rating, comment])
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        rating_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/ratings/{rating.id}/moderation",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"status": "approved"},
        )
        comment_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment.id}/moderation",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"status": "hidden"},
        )

        assert rating_response.status_code == 403
        assert comment_response.status_code == 403


class TestFeedbackObservability:
    """Tests for feedback-specific Prometheus metrics exposure."""

    @staticmethod
    async def _create_user(db_session, email: str, username: str):
        """Create and persist a user for observability tests."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CREATOR,
            preferred_language="en",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.mark.asyncio
    async def test_feedback_metrics_are_exposed_for_success_error_and_moderation(
        self, async_client, db_session
    ):
        """Feedback requests and moderation decisions are exported via the Prometheus endpoint."""
        from app.models import UserRole

        creator = await self._create_user(
            db_session, "metrics-creator@example.com", "metrics_creator"
        )
        commenter = await self._create_user(
            db_session, "metrics-commenter@example.com", "metrics_commenter"
        )
        moderator = await self._create_user(
            db_session, "metrics-moderator@example.com", "metrics_moderator"
        )
        moderator.role = UserRole.MODERATOR

        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator.id,
            title="Observable Feedback Nano",
            duration_minutes=20,
            competency_level=CompetencyLevel.BASIC,
            language="en",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.commit()

        commenter_token, _ = create_access_token(commenter.id, commenter.email, role="creator")
        moderator_token, _ = create_access_token(
            moderator.id,
            moderator.email,
            role="moderator",
        )

        create_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {commenter_token}"},
            json={"content": "Metrics should see this comment."},
        )
        duplicate_response = await async_client.post(
            f"/api/v1/nanos/{nano.id}/comments",
            headers={"Authorization": f"Bearer {commenter_token}"},
            json={"content": "Metrics should reject this duplicate."},
        )

        assert create_response.status_code == 201
        assert duplicate_response.status_code == 409

        comment_id = create_response.json()["comment"]["comment_id"]
        moderation_response = await async_client.patch(
            f"/api/v1/nanos/{nano.id}/comments/{comment_id}/moderation",
            headers={"Authorization": f"Bearer {moderator_token}"},
            json={"status": "approved", "reason": "Looks good"},
        )

        assert moderation_response.status_code == 200

        metrics_response = await async_client.get("/metrics")

        assert metrics_response.status_code == 200
        assert "feedback_requests_total" in metrics_response.text
        assert "feedback_request_duration_seconds" in metrics_response.text
        assert (
            'feedback_requests_total{feedback_type="comment",operation="create",outcome="success"}'
            in metrics_response.text
        )
        assert (
            'feedback_requests_total{feedback_type="comment",operation="create",outcome="client_error"}'
            in metrics_response.text
        )
        assert (
            'feedback_requests_total{feedback_type="comment",operation="moderate",outcome="success"}'
            in metrics_response.text
        )
        assert (
            'feedback_moderation_decisions_total{decision="approved",feedback_type="comment"}'
            in metrics_response.text
        )
