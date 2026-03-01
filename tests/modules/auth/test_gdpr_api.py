"""
Test GDPR API endpoints.

This module tests the HTTP API endpoints for GDPR compliance:
- GET /api/v1/auth/me/export - Export user data
- GET /api/v1/auth/me/consents - Get consent history
- POST /api/v1/auth/me/delete - Request account deletion
- POST /api/v1/auth/me/cancel-deletion - Cancel deletion request
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import User, UserStatus
from app.modules.auth.service import register_user, verify_user_email
from app.schemas import UserRegister


@pytest.mark.asyncio
class TestDataExportAPI:
    """Test data export API endpoint"""

    async def test_export_data_requires_authentication(self, client):
        """Test that data export requires authentication"""
        response = client.get("/api/v1/auth/me/export")
        assert response.status_code == 401  # Unauthorized without auth

    async def test_export_data_success(self, client, db_session):
        """Test successful data export"""
        # Register user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            first_name="Test",
            last_name="User",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email (required for login)
        await verify_user_email(db_session, user_response.id)

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Export data
        response = client.get(
            "/api/v1/auth/me/export",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify exported data
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["status"] == "active"
        assert data["accepted_terms"] is not None
        assert data["accepted_privacy"] is not None
        assert "export_date" in data


@pytest.mark.asyncio
class TestConsentsAPI:
    """Test consent history API endpoint"""

    async def test_get_consents_requires_authentication(self, client):
        """Test that getting consents requires authentication"""
        response = client.get("/api/v1/auth/me/consents")
        assert response.status_code == 401  # Unauthorized

    async def test_get_consents_success(self, client, db_session):
        """Test successful consent retrieval"""
        # Register user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # Get consents
        response = client.get(
            "/api/v1/auth/me/consents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        consents = response.json()

        assert len(consents) == 2
        consent_types = {c["consent_type"] for c in consents}
        assert "terms_of_service" in consent_types
        assert "privacy_policy" in consent_types


@pytest.mark.asyncio
class TestAccountDeletionAPI:
    """Test account deletion API endpoints"""

    async def test_request_deletion_requires_authentication(self, client):
        """Test that deletion request requires authentication"""
        response = client.post(
            "/api/v1/auth/me/delete",
            json={"confirm": True},
        )
        assert response.status_code == 401  # Unauthorized

    async def test_request_deletion_requires_confirmation(self, client, db_session):
        """Test that deletion requires explicit confirmation"""
        # Register and login
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # Try to delete without confirmation
        response = client.post(
            "/api/v1/auth/me/delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": False},
        )

        assert response.status_code == 400
        assert "confirm" in response.json()["detail"].lower()

    async def test_request_deletion_success(self, client, db_session):
        """Test successful deletion request"""
        # Register and login
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # Request deletion
        response = client.post(
            "/api/v1/auth/me/delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True, "reason": "No longer using the service"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["grace_period_days"] == 30
        assert "deletion_scheduled_at" in data
        assert "30 days" in data["message"]

        # Verify user status changed in database
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.status == UserStatus.INACTIVE
        assert user.deletion_requested_at is not None

    async def test_cannot_request_deletion_twice(self, client, db_session):
        """Test that requesting deletion twice fails"""
        # Register and login
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # First deletion request
        response1 = client.post(
            "/api/v1/auth/me/delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True},
        )
        assert response1.status_code == 200

        # Second deletion request should fail
        response2 = client.post(
            "/api/v1/auth/me/delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True},
        )
        assert response2.status_code == 409  # Conflict

    async def test_cancel_deletion_requires_authentication(self, client):
        """Test that cancelling deletion requires authentication"""
        response = client.post("/api/v1/auth/me/cancel-deletion")
        assert response.status_code == 401  # Unauthorized

    async def test_cancel_deletion_success(self, client, db_session):
        """Test successful deletion cancellation"""
        # Register and login
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # Request deletion
        delete_response = client.post(
            "/api/v1/auth/me/delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True},
        )
        assert delete_response.status_code == 200

        # Cancel deletion
        cancel_response = client.post(
            "/api/v1/auth/me/cancel-deletion",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert cancel_response.status_code == 200
        assert "cancelled" in cancel_response.json()["message"].lower()

        # Verify user status restored
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.status == UserStatus.ACTIVE
        assert user.deletion_requested_at is None

    async def test_cancel_deletion_without_request_fails(self, client, db_session):
        """Test that cancelling deletion without request fails"""
        # Register and login (no deletion request)
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Verify email
        await verify_user_email(db_session, user_response.id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        token = login_response.json()["access_token"]

        # Try to cancel non-existent deletion
        response = client.post(
            "/api/v1/auth/me/cancel-deletion",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "no deletion" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestRegistrationWithConsent:
    """Test registration requires consent"""

    async def test_registration_without_terms_fails(self, client):
        """Test that registration without terms acceptance fails"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecureP@ss1",
                "accept_terms": False,
                "accept_privacy": True,
            },
        )

        assert response.status_code == 400
        assert "terms" in response.json()["detail"].lower()

    async def test_registration_without_privacy_fails(self, client):
        """Test that registration without privacy acceptance fails"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecureP@ss1",
                "accept_terms": True,
                "accept_privacy": False,
            },
        )

        assert response.status_code == 400
        assert "privacy" in response.json()["detail"].lower()

    async def test_registration_with_consents_succeeds(self, client, db_session):
        """Test that registration with both consents succeeds"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecureP@ss1",
                "accept_terms": True,
                "accept_privacy": True,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["accepted_terms"] is not None
        assert data["accepted_privacy"] is not None
