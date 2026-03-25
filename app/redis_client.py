"""Redis client for token storage and blacklist management"""

import asyncio
import time
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

_redis_client: Optional[redis.Redis] = None
_fallback_store: dict[str, tuple[str, Optional[float]]] = {}


def _fallback_prune_expired() -> None:
    now = time.time()
    expired_keys = [
        key
        for key, (_, expires_at) in _fallback_store.items()
        if expires_at is not None and expires_at <= now
    ]
    for key in expired_keys:
        _fallback_store.pop(key, None)


def _fallback_set(key: str, value: str, expires_in_seconds: int) -> None:
    _fallback_prune_expired()
    if expires_in_seconds <= 0:
        _fallback_store.pop(key, None)
        return
    expires_at = time.time() + expires_in_seconds
    _fallback_store[key] = (value, expires_at)


def _fallback_get(key: str) -> Optional[str]:
    _fallback_prune_expired()
    entry = _fallback_store.get(key)
    if entry is None:
        return None
    return entry[0]


def _fallback_delete(key: str) -> None:
    _fallback_store.pop(key, None)


def _fallback_get_with_ttl(key: str) -> tuple[Optional[str], Optional[int]]:
    _fallback_prune_expired()
    entry = _fallback_store.get(key)
    if entry is None:
        return None, None

    value, expires_at = entry
    if expires_at is None:
        return value, None

    ttl_seconds = int(expires_at - time.time())
    if ttl_seconds <= 0:
        _fallback_store.pop(key, None)
        return None, None

    return value, ttl_seconds


async def _best_effort_resync_to_redis(
    client: redis.Redis, key: str, value: str, ttl_seconds: Optional[int]
) -> None:
    if ttl_seconds is None or ttl_seconds <= 0:
        return

    try:
        await client.setex(key, ttl_seconds, value)
    except Exception:
        pass


def _is_redis_unavailable(error: Exception) -> bool:
    return isinstance(error, (RedisError, OSError, ConnectionError, asyncio.TimeoutError))


def get_redis_url() -> str:
    """Construct Redis URL from settings.

    Returns:
        Redis connection URL
    """
    settings = get_settings()

    if settings.REDIS_URL:
        return settings.REDIS_URL

    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis() -> redis.Redis:
    """Get Redis client instance.

    Returns:
        Redis client instance.

    Note:
        Uses a singleton pattern with connection pooling for thread-safety.
    """
    global _redis_client

    if _redis_client is None:
        redis_url = get_redis_url()
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection.

    Should be called during application shutdown.
    """
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    _fallback_store.clear()


async def check_redis_health() -> bool:
    """Check Redis health with a ping command.

    Returns:
        True when Redis responds successfully, False otherwise.
    """
    try:
        client = await get_redis()
        return bool(await asyncio.wait_for(client.ping(), timeout=1.0))
    except Exception:
        return False


async def store_refresh_token(user_id: str, token: str, expires_in_seconds: int) -> None:
    """Store refresh token in Redis with expiration.

    Args:
        user_id: User ID
        token: Refresh token
        expires_in_seconds: Token expiration time in seconds
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    try:
        await client.setex(key, expires_in_seconds, token)
    except Exception as error:
        if not _is_redis_unavailable(error):
            raise
        _fallback_set(key, token, expires_in_seconds)


async def get_refresh_token(user_id: str) -> Optional[str]:
    """Get stored refresh token for user.

    Args:
        user_id: User ID

    Returns:
        Refresh token if exists, None otherwise
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    try:
        token = await client.get(key)
    except Exception as error:
        if not _is_redis_unavailable(error):
            raise
        fallback_token, _ = _fallback_get_with_ttl(key)
        return fallback_token

    if token:
        return token

    fallback_token, ttl_seconds = _fallback_get_with_ttl(key)
    if fallback_token is None:
        return None

    await _best_effort_resync_to_redis(client, key, fallback_token, ttl_seconds)
    return fallback_token


async def delete_refresh_token(user_id: str) -> None:
    """Delete refresh token from Redis.

    Args:
        user_id: User ID
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    try:
        await client.delete(key)
    except Exception as error:
        if not _is_redis_unavailable(error):
            raise
    finally:
        _fallback_delete(key)


async def blacklist_token(token: str, expires_in_seconds: int) -> None:
    """Add token to blacklist with expiration.

    Args:
        token: Token to blacklist
        expires_in_seconds: Time until token naturally expires
    """
    client = await get_redis()
    key = f"blacklist:{token}"
    try:
        await client.setex(key, expires_in_seconds, "1")
    except Exception as error:
        if not _is_redis_unavailable(error):
            raise
        _fallback_set(key, "1", expires_in_seconds)


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted.

    Args:
        token: Token to check

    Returns:
        True if blacklisted, False otherwise
    """
    client = await get_redis()
    key = f"blacklist:{token}"
    try:
        exists = await client.exists(key)
    except Exception as error:
        if not _is_redis_unavailable(error):
            raise
        return _fallback_get(key) is not None

    if exists > 0:
        return True

    fallback_value, ttl_seconds = _fallback_get_with_ttl(key)
    if fallback_value is None:
        return False

    await _best_effort_resync_to_redis(client, key, fallback_value, ttl_seconds)
    return True
