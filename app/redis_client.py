"""Redis client for token storage and blacklist management"""

import asyncio
import weakref
from asyncio import AbstractEventLoop
from typing import Optional

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_redis_clients: "weakref.WeakKeyDictionary[AbstractEventLoop, redis.Redis]" = (
    weakref.WeakKeyDictionary()
)


def get_redis_url() -> str:
    """Construct Redis URL from settings.

    Returns:
        Redis connection URL
    """
    if settings.REDIS_URL:
        return settings.REDIS_URL

    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis() -> redis.Redis:
    """Get Redis client instance for the current event loop.

    Returns:
        Redis client instance bound to the current loop.

    Note:
        A separate client is maintained per event loop to avoid cross-loop
        runtime errors in async test environments.
    """
    loop = asyncio.get_running_loop()

    if loop not in _redis_clients:
        redis_url = get_redis_url()
        _redis_clients[loop] = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_clients[loop]


async def close_redis() -> None:
    """Close Redis connection for the current event loop.

    Should be called during application shutdown.
    """
    loop = asyncio.get_running_loop()
    client = _redis_clients.pop(loop, None)

    if client:
        await client.close()


async def store_refresh_token(user_id: str, token: str, expires_in_seconds: int) -> None:
    """Store refresh token in Redis with expiration.

    Args:
        user_id: User ID
        token: Refresh token
        expires_in_seconds: Token expiration time in seconds
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    await client.setex(key, expires_in_seconds, token)


async def get_refresh_token(user_id: str) -> Optional[str]:
    """Get stored refresh token for user.

    Args:
        user_id: User ID

    Returns:
        Refresh token if exists, None otherwise
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    token = await client.get(key)
    return token if token else None


async def delete_refresh_token(user_id: str) -> None:
    """Delete refresh token from Redis.

    Args:
        user_id: User ID
    """
    client = await get_redis()
    key = f"refresh_token:{user_id}"
    await client.delete(key)


async def blacklist_token(token: str, expires_in_seconds: int) -> None:
    """Add token to blacklist with expiration.

    Args:
        token: Token to blacklist
        expires_in_seconds: Time until token naturally expires
    """
    client = await get_redis()
    key = f"blacklist:{token}"
    await client.setex(key, expires_in_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted.

    Args:
        token: Token to check

    Returns:
        True if blacklisted, False otherwise
    """
    client = await get_redis()
    key = f"blacklist:{token}"
    exists = await client.exists(key)
    return exists > 0
