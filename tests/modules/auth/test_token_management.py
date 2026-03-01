"""Tests for JWT Token Management (Story 1.2).

This test file covers:
- JWT token generation with all required claims (sub, iat, exp, role)
- Token validation and verification
- Redis-backed refresh token storage
- Token blacklisting and revocation
- Token refresh with rotation
- Logout functionality
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from jose import jwt

from app.config import get_settings
from app.modules.auth.tokens import (
    TokenData,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.redis_client import (
    blacklist_token,
    delete_refresh_token,
    get_redis,
    get_refresh_token,
    is_token_blacklisted,
    store_refresh_token,
)
from expect import expect

settings = get_settings()


class TestAccessTokenGeneration:
    """Tests for access token generation with enhanced claims."""

    def test_access_token_includes_standard_claims(self) -> None:
        """Test access token includes all required JWT claims.

        Verifies that the generated access token contains all required claims:
        sub, user_id, email, role, type, iat, and exp.
        """
        # Arrange
        user_id = uuid4()
        email = "test@example.com"
        role = "consumer"

        # Act
        token, expires_in = create_access_token(user_id, email, role)

        # Decode without verification to inspect claims
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Assert - All required claims
        expect(payload["sub"]).equal(str(user_id))
        expect(payload["user_id"]).equal(str(user_id))  # Backward compatibility
        expect(payload["email"]).equal(email)
        expect(payload["role"]).equal(role)
        expect(payload["type"]).equal("access")
        expect(payload).has_keys("iat", "exp")

        # Assert - Verify expiry time is configured correctly
        expect(expires_in).equal(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    def test_access_token_expiry_is_15_minutes(self) -> None:
        """Test access token expires in 15 minutes.

        Verifies that the token's exp claim is approximately 15 minutes
        from the iat claim, matching the configured expiration time.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token, _ = create_access_token(user_id, "test@example.com")

        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # Assert - Check expiry is approximately 15 minutes from issue time
        expected_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        actual_delta = exp - iat
        expect(abs((actual_delta - expected_delta).total_seconds())).to_be_less_than(2)

    def test_access_token_with_different_roles(self) -> None:
        """Test access tokens can be created with different roles.

        Verifies that the token generation function correctly includes
        the specified role in the token payload.
        """
        # Arrange
        user_id = uuid4()
        email = "admin@example.com"

        # Act & Assert
        for role in ["consumer", "creator", "admin", "moderator"]:
            token, _ = create_access_token(user_id, email, role)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            expect(payload["role"]).equal(role)


class TestRefreshTokenGeneration:
    """Tests for refresh token generation."""

    def test_refresh_token_includes_standard_claims(self) -> None:
        """Test refresh token includes all required JWT claims.

        Verifies that the generated refresh token contains all required claims:
        sub, user_id, email, role, type, iat, and exp.
        """
        # Arrange
        user_id = uuid4()
        email = "test@example.com"
        role = "creator"

        # Act
        token, expires_in = create_refresh_token(user_id, email, role)

        # Decode and Assert
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        expect(payload["sub"]).equal(str(user_id))
        expect(payload["user_id"]).equal(str(user_id))
        expect(payload["email"]).equal(email)
        expect(payload["role"]).equal(role)
        expect(payload["type"]).equal("refresh")
        expect(payload).has_keys("iat", "exp")

        # Assert - Verify expiry time is ~7 days
        expect(expires_in).equal(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

    def test_refresh_token_expiry_is_7_days(self) -> None:
        """Test refresh token expires in 7 days.

        Verifies that the token's exp claim is approximately 7 days
        from the iat claim, matching the configured expiration time.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token, _ = create_refresh_token(user_id, "test@example.com")

        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # Assert
        expected_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        actual_delta = exp - iat
        expect(abs((actual_delta - expected_delta).total_seconds())).to_be_less_than(2)


class TestTokenVerification:
    """Tests for token verification with enhanced claims."""

    def test_verify_valid_access_token(self) -> None:
        """Test valid access token can be verified successfully.

        Verifies that token verification correctly extracts all user
        information from a valid access token.
        """
        # Arrange
        user_id = uuid4()
        email = "test@example.com"
        role = "consumer"

        # Act
        token, _ = create_access_token(user_id, email, role)
        token_data = verify_token(token, token_type="access")

        # Assert
        expect(token_data).is_not_none()
        expect(isinstance(token_data, TokenData)).to_be_true()
        expect(token_data.user_id).equal(user_id)
        expect(token_data.email).equal(email)
        expect(token_data.role).equal(role)
        expect(isinstance(token_data.exp, datetime)).to_be_true()
        expect(isinstance(token_data.iat, datetime)).to_be_true()

    def test_verify_token_extracts_role(self) -> None:
        """Test token verification extracts role claim correctly.

        Ensures that the role is properly extracted from the token
        and available in the TokenData object.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token, _ = create_access_token(user_id, "admin@example.com", "admin")
        token_data = verify_token(token, token_type="access")

        # Assert
        expect(token_data.role).equal("admin")

    def test_verify_token_wrong_type_returns_none(self) -> None:
        """Test token verification fails if type mismatch.

        Verifies that attempting to verify an access token as a refresh
        token fails by returning None.
        """
        # Arrange
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Act: Try to verify access token as refresh token
        token_data = verify_token(token, token_type="refresh")

        # Assert
        expect(token_data).is_none()

    def test_verify_expired_token_returns_none(self) -> None:
        """Test expired token verification fails.

        Verifies that attempting to verify an expired token returns None.
        """
        # Arrange
        user_id = uuid4()

        # Create token that expired 1 hour ago
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "email": "test@example.com",
            "role": "consumer",
            "iat": int((past_time - timedelta(hours=1)).timestamp()),
            "exp": int(past_time.timestamp()),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # Act
        token_data = verify_token(token, token_type="access")

        # Assert
        expect(token_data).is_none()

    def test_verify_token_with_invalid_signature_returns_none(self) -> None:
        """Test token with invalid signature fails verification.

        Verifies that tampering with the token results in verification failure.
        """
        # Arrange
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"

        # Act
        token_data = verify_token(tampered_token, token_type="access")

        # Assert
        expect(token_data).is_none()


class TestRedisTokenStorage:
    """Tests for Redis-backed refresh token storage."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_refresh_token(self) -> None:
        """Test refresh tokens can be stored and retrieved from Redis.

        Verifies that tokens stored in Redis can be retrieved with
        their original values intact.
        """
        # Arrange
        user_id = str(uuid4())
        token = "test_refresh_token_12345"
        expires_in = 3600  # 1 hour

        # Act
        await store_refresh_token(user_id, token, expires_in)
        retrieved_token = await get_refresh_token(user_id)

        # Assert
        expect(retrieved_token).equal(token)

    @pytest.mark.asyncio
    async def test_refresh_token_expires_in_redis(self) -> None:
        """Test refresh tokens expire in Redis after TTL.

        Verifies that tokens automatically expire from Redis after
        the configured ttl has elapsed.
        """
        # Arrange
        user_id = str(uuid4())
        token = "short_lived_token"
        expires_in = 1  # 1 second

        # Act
        await store_refresh_token(user_id, token, expires_in)

        # Wait for expiration
        await asyncio.sleep(2)

        # Retrieve after expiration
        retrieved_token = await get_refresh_token(user_id)

        # Assert
        expect(retrieved_token).is_none()

    @pytest.mark.asyncio
    async def test_delete_refresh_token(self) -> None:
        """Test refresh tokens can be deleted from Redis.

        Verifies that tokens can be explicitly deleted and are no longer
        accessible after deletion.
        """
        # Arrange
        user_id = str(uuid4())
        token = "test_token_to_delete"

        # Act
        await store_refresh_token(user_id, token, 3600)
        await delete_refresh_token(user_id)

        # Retrieve after deletion
        retrieved_token = await get_refresh_token(user_id)

        # Assert
        expect(retrieved_token).is_none()

    @pytest.mark.asyncio
    async def test_get_nonexistent_refresh_token(self) -> None:
        """Test getting non-existent token returns None.

        Verifies that attempting to retrieve a token for a user
        without a stored token returns None gracefully.
        """
        # Arrange
        user_id = str(uuid4())

        # Act
        retrieved_token = await get_refresh_token(user_id)

        # Assert
        expect(retrieved_token).is_none()


class TestTokenBlacklisting:
    """Tests for token blacklist/revocation mechanism."""

    @pytest.mark.asyncio
    async def test_blacklist_token(self) -> None:
        """Test tokens can be added to blacklist.

        Verifies that a token can be blacklisted and is subsequently
        detected as blacklisted.
        """
        # Arrange
        token = "access_token_to_blacklist"
        expires_in = 3600

        # Act
        await blacklist_token(token, expires_in)
        is_blacklisted = await is_token_blacklisted(token)

        # Assert
        expect(is_blacklisted).to_be_true()

    @pytest.mark.asyncio
    async def test_non_blacklisted_token(self) -> None:
        """Test non-blacklisted tokens are not detected as blacklisted.

        Verifies that a token that has not been blacklisted returns False
        when checked.
        """
        # Arrange
        token = "clean_token"

        # Act
        is_blacklisted = await is_token_blacklisted(token)

        # Assert
        expect(is_blacklisted).to_be_false()

    @pytest.mark.asyncio
    async def test_blacklist_expires_with_token(self) -> None:
        """Test blacklist entries expire along with token TTL.

        Verifies that blacklist entries are automatically removed after
        the TTL expires, allowing tokens to be reissued if needed.
        """
        # Arrange
        token = "short_blacklist_token"
        expires_in = 1  # 1 second

        # Act
        await blacklist_token(token, expires_in)
        expect(await is_token_blacklisted(token)).to_be_true()

        # Wait for expiration
        await asyncio.sleep(2)

        # Assert
        is_blacklisted = await is_token_blacklisted(token)
        expect(is_blacklisted).to_be_false()


class TestTokenClaims:
    """Tests for JWT claims compliance."""

    def test_token_has_no_sensitive_data(self) -> None:
        """Test tokens do not contain sensitive information.

        Verifies that sensitive fields like password hashes are not
        included in the token payload.
        """
        # Arrange
        user_id = uuid4()
        email = "test@example.com"

        # Act
        token, _ = create_access_token(user_id, email)

        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Assert - Ensure no sensitive data in token
        expect("password" in payload).to_be_false()
        expect("password_hash" in payload).to_be_false()
        expect("secret" in payload.get("email", "")).to_be_false()

    def test_token_signature_is_hs256(self) -> None:
        """Test tokens use HS256 algorithm.

        Verifies that all tokens are signed using the HS256 algorithm
        as specified in the requirements.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token, _ = create_access_token(user_id, "test@example.com")

        # Decode header to check algorithm
        from jose import jwt as jose_jwt

        header = jose_jwt.get_unverified_header(token)

        # Assert
        expect(header["alg"]).equal("HS256")

    def test_token_uses_secret_from_config(self) -> None:
        """Test token uses SECRET_KEY from configuration.

        Verifies that tokens can only be decoded with the correct secret
        from configuration, and fail with an incorrect secret.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token, _ = create_access_token(user_id, "test@example.com")

        # Assert - Should decode successfully with correct secret
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        expect(payload).is_not_none()

        # Assert - Should fail with wrong secret
        with pytest.raises(Exception):
            jwt.decode(token, "wrong_secret", algorithms=[settings.ALGORITHM])


class TestTokenErrorHandling:
    """Tests for token error handling and edge cases."""

    def test_verify_token_with_missing_role_defaults_to_consumer(self) -> None:
        """Test token without role claim defaults to 'consumer'.

        Verifies that if a token is missing the role claim, it defaults
        to 'consumer' to ensure graceful degradation.
        """
        # Arrange
        user_id = uuid4()
        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "email": "test@example.com",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "type": "access",
            # Note: no 'role' claim
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # Act
        token_data = verify_token(token, token_type="access")

        # Assert
        expect(token_data).is_not_none()
        expect(token_data.role).equal("consumer")

    def test_verify_token_with_missing_iat_uses_current_time(self) -> None:
        """Test token without iat claim uses current time.

        Verifies that if the iat claim is missing, the verification
        process uses the current time as a fallback.
        """
        # Arrange
        user_id = uuid4()
        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "email": "test@example.com",
            "role": "consumer",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "type": "access",
            # Note: no 'iat' claim
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # Act
        token_data = verify_token(token, token_type="access")

        # Assert
        expect(token_data).is_not_none()
        # iat should be close to current time (within 5 seconds)
        now = datetime.now(timezone.utc)
        expect(abs((token_data.iat - now).total_seconds())).to_be_less_than(5)
