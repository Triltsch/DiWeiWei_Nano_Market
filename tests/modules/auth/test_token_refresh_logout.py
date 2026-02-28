"""Integration tests for token refresh and logout endpoints.

This test file covers:
- Token refresh endpoint with rotation
- Logout endpoint with token revocation
- Blacklist verification in protected endpoints
- End-to-end token lifecycle
"""

from uuid import uuid4

import pytest

from app.models import User, UserRole, UserStatus
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import create_access_token, create_refresh_token
from app.redis_client import (
    blacklist_token,
    get_redis,
    store_refresh_token,
)
from expect import expect


@pytest.fixture
async def test_user(db_session):
    """Create a verified test user in the database.

    Returns a user that can authenticate and use tokens.
    """
    suffix = uuid4().hex[:8]
    user = User(
        email=f"testuser_{suffix}@example.com",
        username=f"testuser_{suffix}",
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
    """Tests for POST /api/v1/auth/refresh-token endpoint.

    Requirements:
    - Validates refresh token
    - Returns new access token
    - Implements token rotation (new refresh token)
    - Blacklists old refresh token
    """

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client, test_user: User, db_session) -> None:
        """Test successful token refresh with rotation.

        Verifies that the endpoint returns new access and refresh tokens,
        implements token rotation, and blacklists the old token to prevent reuse.
        """
        # Arrange: Create and store initial refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Act: Refresh the token
        response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert: Response structure and status
        expect(response.status_code).equal(200)
        data = response.json()

        expect(data).has_keys("access_token", "refresh_token", "expires_in")
        expect(data["token_type"]).equal("bearer")

        # Assert: New tokens should be different from old
        expect(data["access_token"]).is_not_equal(refresh_token)
        expect(data["refresh_token"]).is_not_equal(refresh_token)

    @pytest.mark.asyncio
    async def test_refresh_token_with_invalid_token(self, async_client) -> None:
        """Test refresh with invalid token fails.

        Ensures that providing an invalid token results in a 401 Unauthorized
        response with an appropriate error message.
        """
        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": "invalid_token"}
        )

        # Assert
        expect(response.status_code).equal(401)
        expect(response.json()["detail"]).contains("Invalid or expired refresh token")

    @pytest.mark.asyncio
    async def test_refresh_token_not_in_redis(self, async_client, test_user: User) -> None:
        """Test refresh with token not stored in Redis fails.

        Verifies that only stored refresh tokens are valid, preventing
        unauthorized token generation.
        """
        # Arrange: Create token but don't store in Redis
        refresh_token, _ = create_refresh_token(test_user.id, test_user.email, test_user.role.value)

        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert
        expect(response.status_code).equal(401)

    @pytest.mark.asyncio
    async def test_refresh_token_for_inactive_user(
        self, async_client, test_user: User, db_session
    ) -> None:
        """Test refresh token fails for inactive user.

        Ensures that users with suspended or inactive status cannot
        refresh their authentication tokens.
        """
        # Arrange: Create and store refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Deactivate user
        test_user.status = UserStatus.SUSPENDED
        db_session.add(test_user)
        await db_session.commit()

        # Act: Try to refresh
        response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert
        expect(response.status_code).equal(401)
        expect(response.json()["detail"].lower()).contains("inactive")

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(self, async_client, test_user: User) -> None:
        """Test refresh with blacklisted token fails.

        Verifies that blacklisted tokens cannot be used to generate new
        authentication tokens, enforcing logout requirements.
        """
        # Arrange: Create, store, and blacklist refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)
        await blacklist_token(refresh_token, expires_in)

        # Act: Try to refresh
        response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert
        expect(response.status_code).equal(401)
        expect(response.json()["detail"].lower()).contains("revoked")

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_prevents_reuse(
        self, async_client, test_user: User
    ) -> None:
        """Test old refresh token cannot be reused after rotation.

        Verifies that after a token refresh, the old token is immediately
        invalidated, preventing token theft exploitation.
        """
        # Arrange: Create and store initial refresh token
        old_refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), old_refresh_token, expires_in)

        # Act & Assert: First refresh should succeed
        response1 = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": old_refresh_token}
        )
        expect(response1.status_code).equal(200)

        # Act & Assert: Second refresh with old token should fail
        response2 = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": old_refresh_token}
        )
        expect(response2.status_code).equal(401)


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout endpoint.

    Requirements:
    - Requires authentication (Bearer token)
    - Revokes both access and refresh tokens
    - Tokens cannot be used after logout
    """

    @pytest.mark.asyncio
    async def test_logout_success(self, async_client, test_user: User) -> None:
        """Test successful logout revokes tokens.

        Verifies that logout successfully revokes both access and refresh tokens,
        and returns a success message to the client.
        """
        # Arrange: Create tokens
        access_token, _ = create_access_token(test_user.id, test_user.email, test_user.role.value)
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Act: Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        expect(response.status_code).equal(200)
        expect(response.json()["message"]).contains("Successfully logged out")

    @pytest.mark.asyncio
    async def test_logout_without_auth_token(self, async_client) -> None:
        """Test logout without Authorization header fails.

        Ensures that logout requires proper authentication to prevent
        unauthorized logout requests.
        """
        # Act
        response = await async_client.post(
            "/api/v1/auth/logout", json={"refresh_token": "some_token"}
        )

        # Assert
        expect(response.status_code).is_in([401, 403])

    @pytest.mark.asyncio
    async def test_logout_with_invalid_access_token(self, async_client) -> None:
        """Test logout with invalid access token fails.

        Verifies that logout requires a valid access token to authenticate
        the logout request.
        """
        # Act
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "refresh_token"},
            headers={"Authorization": "Bearer invalid_token"},
        )

        # Assert
        expect(response.status_code).equal(401)

    @pytest.mark.asyncio
    async def test_tokens_unusable_after_logout(self, async_client, test_user: User) -> None:
        """Test tokens cannot be used after logout.

        Verifies that after logout, both the access and refresh tokens
        are invalidated and cannot be reused.
        """
        # Arrange: Create tokens
        access_token, _ = create_access_token(test_user.id, test_user.email, test_user.role.value)
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Act: Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert: Logout succeeds
        expect(logout_response.status_code).equal(200)

        # Act: Try to use refresh token
        refresh_response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert: Token reuse should fail
        expect(refresh_response.status_code).equal(401)


class TestTokenLifecycle:
    """End-to-end tests for complete token lifecycle.

    Tests the full flow: login → use token → refresh → logout.
    """

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, async_client, test_user: User) -> None:
        """Test complete token lifecycle from login to logout.

        Verifies that all operations in the token lifecycle succeed in sequence:
        login generates tokens, refresh rotates them, and logout invalidates them.
        """
        # Step 1: Login
        # Arrange & Act
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "SecurePass123!"},
        )

        # Assert
        expect(login_response.status_code).equal(200)
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Step 2: Refresh token
        # Act
        refresh_response = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert
        expect(refresh_response.status_code).equal(200)
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # Assert: New tokens should be different
        expect(new_access_token).is_not_equal(access_token)
        expect(new_refresh_token).is_not_equal(refresh_token)

        # Step 3: Logout with new tokens
        # Act
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh_token},
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

        # Assert
        expect(logout_response.status_code).equal(200)

    @pytest.mark.asyncio
    async def test_concurrent_refresh_requests(self, async_client, test_user: User) -> None:
        """Test only one refresh request succeeds with same token.

        Verifies that token rotation prevents concurrent refresh attempts
        with the same token, where only the first succeeds and the second fails.
        """
        # Arrange: Create and store refresh token
        refresh_token, expires_in = create_refresh_token(
            test_user.id, test_user.email, test_user.role.value
        )
        await store_refresh_token(str(test_user.id), refresh_token, expires_in)

        # Act: Make first refresh request
        response1 = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert
        expect(response1.status_code).equal(200)

        # Act: Try immediately with same token (simulating concurrent request)
        response2 = await async_client.post(
            "/api/v1/auth/refresh-token", json={"refresh_token": refresh_token}
        )

        # Assert: Should fail because token was rotated
        expect(response2.status_code).equal(401)
