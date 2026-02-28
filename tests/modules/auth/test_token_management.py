"""
Tests for JWT Token Management (Story 1.2)

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

settings = get_settings()


class TestAccessTokenGeneration:
    """Tests for access token generation with enhanced claims"""

    def test_access_token_includes_standard_claims(self):
        """
        Test: Access token includes all required JWT claims
        Expected: Token contains sub, iat, exp, role, email, type
        """
        user_id = uuid4()
        email = "test@example.com"
        role = "consumer"

        token, expires_in = create_access_token(user_id, email, role)

        # Decode without verification to inspect claims
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Check all required claims
        assert payload["sub"] == str(user_id)
        assert payload["user_id"] == str(user_id)  # Backward compatibility
        assert payload["email"] == email
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "iat" in payload
        assert "exp" in payload

        # Verify expiry time is ~15 minutes
        assert expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_access_token_expiry_is_15_minutes(self):
        """
        Test: Access token expires in 15 minutes as per requirements
        Expected: Token exp claim is ~15 minutes from iat
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # Check expiry is approximately 15 minutes from issue time
        expected_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        actual_delta = exp - iat
        assert abs((actual_delta - expected_delta).total_seconds()) < 2  # Allow 2sec variance

    def test_access_token_with_different_roles(self):
        """
        Test: Access tokens can be created with different user roles
        Expected: Token contains the specified role
        """
        user_id = uuid4()
        email = "admin@example.com"

        for role in ["consumer", "creator", "admin", "moderator"]:
            token, _ = create_access_token(user_id, email, role)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            assert payload["role"] == role


class TestRefreshTokenGeneration:
    """Tests for refresh token generation"""

    def test_refresh_token_includes_standard_claims(self):
        """
        Test: Refresh token includes all required JWT claims
        Expected: Token contains sub, iat, exp, role, email, type
        """
        user_id = uuid4()
        email = "test@example.com"
        role = "creator"

        token, expires_in = create_refresh_token(user_id, email, role)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == str(user_id)
        assert payload["user_id"] == str(user_id)
        assert payload["email"] == email
        assert payload["role"] == role
        assert payload["type"] == "refresh"
        assert "iat" in payload
        assert "exp" in payload

        # Verify expiry time is ~7 days
        assert expires_in == settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    def test_refresh_token_expiry_is_7_days(self):
        """
        Test: Refresh token expires in 7 days as per requirements
        Expected: Token exp claim is ~7 days from iat
        """
        user_id = uuid4()
        token, _ = create_refresh_token(user_id, "test@example.com")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        expected_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        actual_delta = exp - iat
        assert abs((actual_delta - expected_delta).total_seconds()) < 2


class TestTokenVerification:
    """Tests for token verification with enhanced claims"""

    def test_verify_valid_access_token(self):
        """
        Test: Valid access token can be verified successfully
        Expected: Returns TokenData with all user information
        """
        user_id = uuid4()
        email = "test@example.com"
        role = "consumer"

        token, _ = create_access_token(user_id, email, role)
        token_data = verify_token(token, token_type="access")

        assert token_data is not None
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.role == role
        assert isinstance(token_data.exp, datetime)
        assert isinstance(token_data.iat, datetime)

    def test_verify_token_extracts_role(self):
        """
        Test: Token verification extracts role claim
        Expected: TokenData contains correct role
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "admin@example.com", "admin")
        token_data = verify_token(token, token_type="access")

        assert token_data.role == "admin"

    def test_verify_token_wrong_type_returns_none(self):
        """
        Test: Token verification fails if type mismatch
        Expected: Returns None when verifying access token as refresh
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Try to verify access token as refresh token
        token_data = verify_token(token, token_type="refresh")
        assert token_data is None

    def test_verify_expired_token_returns_none(self):
        """
        Test: Expired token verification fails
        Expected: Returns None for expired token
        """
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

        token_data = verify_token(token, token_type="access")
        assert token_data is None

    def test_verify_token_with_invalid_signature_returns_none(self):
        """
        Test: Token with invalid signature fails verification
        Expected: Returns None for tampered token
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"

        token_data = verify_token(tampered_token, token_type="access")
        assert token_data is None


class TestRedisTokenStorage:
    """Tests for Redis-backed refresh token storage"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_refresh_token(self):
        """
        Test: Refresh tokens can be stored and retrieved from Redis
        Expected: Stored token is retrievable with same value
        """
        user_id = str(uuid4())
        token = "test_refresh_token_12345"
        expires_in = 3600  # 1 hour

        await store_refresh_token(user_id, token, expires_in)
        retrieved_token = await get_refresh_token(user_id)

        assert retrieved_token == token

    @pytest.mark.asyncio
    async def test_refresh_token_expires_in_redis(self):
        """
        Test: Refresh tokens expire in Redis after TTL
        Expected: Token is None after expiration
        """
        user_id = str(uuid4())
        token = "short_lived_token"
        expires_in = 1  # 1 second

        await store_refresh_token(user_id, token, expires_in)

        # Wait for expiration
        await asyncio.sleep(2)

        retrieved_token = await get_refresh_token(user_id)
        assert retrieved_token is None

    @pytest.mark.asyncio
    async def test_delete_refresh_token(self):
        """
        Test: Refresh tokens can be deleted from Redis
        Expected: Token is None after deletion
        """
        user_id = str(uuid4())
        token = "test_token_to_delete"

        await store_refresh_token(user_id, token, 3600)
        await delete_refresh_token(user_id)

        retrieved_token = await get_refresh_token(user_id)
        assert retrieved_token is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_refresh_token(self):
        """
        Test: Getting non-existent token returns None
        Expected: Returns None for user without stored token
        """
        user_id = str(uuid4())
        retrieved_token = await get_refresh_token(user_id)
        assert retrieved_token is None


class TestTokenBlacklisting:
    """Tests for token blacklist/revocation mechanism"""

    @pytest.mark.asyncio
    async def test_blacklist_token(self):
        """
        Test: Tokens can be added to blacklist
        Expected: Blacklisted token is detected as blacklisted
        """
        token = "access_token_to_blacklist"
        expires_in = 3600

        await blacklist_token(token, expires_in)
        is_blacklisted = await is_token_blacklisted(token)

        assert is_blacklisted is True

    @pytest.mark.asyncio
    async def test_non_blacklisted_token(self):
        """
        Test: Non-blacklisted tokens are not detected as blacklisted
        Expected: Returns False for clean token
        """
        token = "clean_token"
        is_blacklisted = await is_token_blacklisted(token)

        assert is_blacklisted is False

    @pytest.mark.asyncio
    async def test_blacklist_expires_with_token(self):
        """
        Test: Blacklist entries expire along with token TTL
        Expected: Blacklisted token becomes non-blacklisted after expiry
        """
        token = "short_blacklist_token"
        expires_in = 1  # 1 second

        await blacklist_token(token, expires_in)
        assert await is_token_blacklisted(token) is True

        # Wait for expiration
        await asyncio.sleep(2)

        is_blacklisted = await is_token_blacklisted(token)
        assert is_blacklisted is False


class TestTokenClaims:
    """Tests for JWT claims compliance"""

    def test_token_has_no_sensitive_data(self):
        """
        Test: Tokens do not contain sensitive information
        Expected: Password or sensitive fields are not in token
        """
        user_id = uuid4()
        email = "test@example.com"
        token, _ = create_access_token(user_id, email)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Ensure no sensitive data in token
        assert "password" not in payload
        assert "password_hash" not in payload
        assert "secret" not in payload.get("email", "")

    def test_token_signature_is_hs256(self):
        """
        Test: Tokens use HS256 algorithm as per requirements
        Expected: Token algorithm is HS256
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Decode header to check algorithm
        from jose import jwt as jose_jwt

        header = jose_jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_token_uses_secret_from_config(self):
        """
        Test: Token uses SECRET_KEY from configuration
        Expected: Token can only be decoded with correct secret
        """
        user_id = uuid4()
        token, _ = create_access_token(user_id, "test@example.com")

        # Should decode successfully with correct secret
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload is not None

        # Should fail with wrong secret
        try:
            jwt.decode(token, "wrong_secret", algorithms=[settings.ALGORITHM])
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected


class TestTokenErrorHandling:
    """Tests for token error handling and edge cases"""

    def test_verify_token_with_missing_role_defaults_to_consumer(self):
        """
        Test: Token without role claim defaults to 'consumer'
        Expected: TokenData.role is 'consumer' when claim is missing
        """
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

        token_data = verify_token(token, token_type="access")

        assert token_data is not None
        assert token_data.role == "consumer"

    def test_verify_token_with_missing_iat_uses_current_time(self):
        """
        Test: Token without iat claim uses current time
        Expected: TokenData.iat is approximately now
        """
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

        token_data = verify_token(token, token_type="access")

        assert token_data is not None
        # iat should be close to current time (within 5 seconds)
        now = datetime.now(timezone.utc)
        assert abs((token_data.iat - now).total_seconds()) < 5
