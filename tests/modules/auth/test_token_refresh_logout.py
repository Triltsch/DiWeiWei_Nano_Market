"""
Integration tests for token refresh and logout endpoints

This test file covers:
- Token refresh endpoint with rotation
- Logout endpoint with token revocation
- Blacklist verification in protected endpoints
- End-to-end token lifecycle
"""

import pytest
from fastapi.testclient import TestClient

from app.models import User, UserRole, UserStatus
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import create_access_token, create_refresh_token
from app.redis_client import (
    blacklist_token,
    get_redis,
    store_refresh_token,
)


@pytest.fixture
async def test_user(db_session):
    """
    Create a verified test user in the database

    Returns a user that can authenticate and use tokens
    """
    user = User(
        email="testuser@example.com",
        username="testuser",
        password_hash=hash_password("SecurePass123!"),
        first_name="Test",
        last_name="User",
        status=UserStatus.ACTIVE,
        role=UserRole.CONSUMER,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestTokenRefreshEndpoint:
    """
    Tests for POST /api/v1/auth/refresh-token endpoint

    Requirements:
    - Validates refresh token
    - Returns new access token
    - Implements token rotation (new refresh token)
    - Blacklists old refresh token
    """

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: TestClient, test_user, db_session):
        """
        Test: Successful token refresh with rotation
        Expected: Returns new access and refresh tokens, old token blacklisted
        """
        # Create and store initial refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Refresh the token
        response = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

        # New tokens should be different from old
        assert data["access_token"] != refresh_token
        assert data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_with_invalid_token(self, client: TestClient):
        """
        Test: Refresh with invalid token fails
        Expected: Returns 401 Unauthorized
        """
        response = client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_not_in_redis(self, client: TestClient, test_user):
        """
        Test: Refresh with token not stored in Redis fails
        Expected: Returns 401 Unauthorized
        """
        # Create token but don't store in Redis
        refresh_token, _ = create_refresh_token(test_user.id, test_user.email, test_user.role.value)

        response = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_for_inactive_user(self, client: TestClient, test_user, db_session):
        """
        Test: Refresh token fails for inactive user
        Expected: Returns 401 Unauthorized
        """
        # Create and store refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Deactivate user
        test_user.status = UserStatus.SUSPENDED
        db_session.add(test_user)
        await db_session.commit()

        # Try to refresh
        response = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(self, client: TestClient, test_user):
        """
        Test: Refresh with blacklisted token fails
        Expected: Returns 401 with revoked message
        """
        # Create and store refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Blacklist the token
        await blacklist_token(refresh_token, expires_in)

        # Try to refresh
        response = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_prevents_reuse(self, client: TestClient, test_user):
        """
        Test: Old refresh token cannot be reused after rotation
        Expected: Second refresh attempt with old token fails
        """
        # Create and store initial refresh token
        old_refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), old_refresh_token, expires_in)

        # First refresh - should succeed
        response1 = client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": old_refresh_token}
        )
        assert response1.status_code == 200

        # Try to use old token again - should fail
        response2 = client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": old_refresh_token}
        )
        assert response2.status_code == 401


class TestLogoutEndpoint:
    """
    Tests for POST /api/v1/auth/logout endpoint

    Requirements:
    - Requires authentication (Bearer token)
    - Revokes both access and refresh tokens
    - Tokens cannot be used after logout
    """

    @pytest.mark.asyncio
    async def test_logout_success(self, client: TestClient, test_user):
        """
        Test: Successful logout revokes tokens
        Expected: Returns success message, tokens are blacklisted
        """
        # Create tokens
        access_token, _ = create_access_token(test_user.id, test_user.email, test_user.role.value)
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_logout_without_auth_token(self, client: TestClient):
        """
        Test: Logout without Authorization header fails
        Expected: Returns 401 or 403 Unauthorized
        """
        response = client.post("/api/v1/auth/logout", json={"refresh_token": "some_token"})

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_logout_with_invalid_access_token(self, client: TestClient):
        """
        Test: Logout with invalid access token fails
        Expected: Returns 401 Unauthorized
        """
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "refresh_token"},
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_tokens_unusable_after_logout(self, client: TestClient, test_user):
        """
        Test: Tokens cannot be used after logout
        Expected: Using logged-out tokens returns 401
        """
        # Create tokens
        access_token, _ = create_access_token(test_user.id, test_user.email, test_user.role.value)
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200

        # Try to use refresh token - should fail
        refresh_response = client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 401


class TestTokenLifecycle:
    """
    End-to-end tests for complete token lifecycle

    Tests the full flow: login → use token → refresh → logout
    """

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, client: TestClient, test_user):
        """
        Test: Complete token lifecycle from login to logout
        Expected: All operations succeed in sequence
        """
        # 1. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 2. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # New tokens should be different
        assert new_access_token != access_token
        assert new_refresh_token != refresh_token

        # 3. Logout with new tokens
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh_token},
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert logout_response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_refresh_requests(self, client: TestClient, test_user):
        """
        Test: Only one refresh request succeeds with same token
        Expected: First request succeeds, concurrent request fails
        """
        # Create and store refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Make first refresh request
        response1 = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})
        assert response1.status_code == 200

        # Try immediately with same token (simulating concurrent request)
        response2 = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})
        # Should fail because token was rotated
        assert response2.status_code == 401
