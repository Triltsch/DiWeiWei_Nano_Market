"""Router for chat session and message endpoints."""

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.modules.auth.middleware import (
    ROLE_ADMIN,
    ROLE_CONSUMER,
    ROLE_CREATOR,
    ROLE_MODERATOR,
    require_any_role,
)
from app.modules.auth.tokens import TokenData
from app.modules.chat.content_filter import SpamContentFilter
from app.modules.chat.schemas import (
    ChatMessageCreateRequest,
    ChatMessageCreateResponse,
    ChatMessageListResponse,
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
    ChatSessionListResponse,
)
from app.modules.chat.service import (
    create_or_get_chat_session,
    list_chat_sessions,
    list_messages,
    send_message,
)
from app.monitoring import SPAM_MESSAGE_RATE_LIMIT_429_TOTAL
from app.security.rate_limit import SlidingWindowRateLimiter

settings = get_settings()
logger = logging.getLogger(__name__)


CHAT_MESSAGE_RATE_LIMITER = SlidingWindowRateLimiter(
    max_requests=(
        settings.RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS
        + settings.RATE_LIMIT_CHAT_MESSAGE_BURST_REQUESTS
    ),
    window_seconds=settings.RATE_LIMIT_CHAT_MESSAGE_WINDOW_SECONDS,
)
CHAT_CONTENT_FILTER = SpamContentFilter()


async def _enforce_chat_message_rate_limit(user_id: str, session_id: UUID) -> None:
    """Apply per-user rate limiting for message submissions."""
    key = f"chat_message:{user_id}:{session_id}"
    allowed, retry_after_seconds = await CHAT_MESSAGE_RATE_LIMITER.check(key)
    if allowed:
        return

    SPAM_MESSAGE_RATE_LIMIT_429_TOTAL.labels(
        endpoint="POST /api/v1/chats/{session_id}/messages"
    ).inc()

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            "You're sending messages too fast. " f"Try again in {retry_after_seconds} seconds."
        ),
        headers={"Retry-After": str(retry_after_seconds)},
    )


def _enforce_chat_content_filter(content: str) -> None:
    """Apply spam-content validation before message persistence."""
    result = CHAT_CONTENT_FILTER.evaluate(content)
    if result.allowed:
        return

    reason = result.reason or "content_filter_blocked"
    logger.info("Blocked chat message by content filter", extra={"reason": reason})
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Message blocked: {reason}",
    )


def get_chat_router(prefix: str = "/api/v1/chats", tags: list[str] | None = None) -> APIRouter:
    """Create and configure router for chat session and message endpoints."""
    if tags is None:
        tags = ["Chat"]

    router = APIRouter(prefix=prefix, tags=tags)
    chat_access_dependency = require_any_role(
        ROLE_CONSUMER,
        ROLE_CREATOR,
        ROLE_MODERATOR,
        ROLE_ADMIN,
    )

    @router.post(
        "",
        response_model=ChatSessionCreateResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create or reuse chat session for a Nano",
        responses={
            401: {"description": "Missing or invalid authentication token"},
            403: {"description": "User is not allowed to open this chat session"},
            404: {"description": "Published Nano not found"},
        },
    )
    async def create_chat_session(
        payload: ChatSessionCreateRequest,
        token_data: Annotated[TokenData, Depends(chat_access_dependency)],
        response: Response,
        db: AsyncSession = Depends(get_db),
    ) -> ChatSessionCreateResponse:
        """Create a chat session or reuse the existing one for the same participants and Nano."""
        result = await create_or_get_chat_session(
            db=db,
            payload=payload,
            current_user=token_data,
        )
        if result.meta.get("reused"):
            response.status_code = status.HTTP_200_OK
        return result

    @router.get(
        "",
        response_model=ChatSessionListResponse,
        summary="List chat sessions for current user",
        responses={
            401: {"description": "Missing or invalid authentication token"},
        },
    )
    async def get_chat_sessions(
        token_data: Annotated[TokenData, Depends(chat_access_dependency)],
        nano_id: Annotated[
            UUID | None,
            Query(description="Optional Nano filter for sessions"),
        ] = None,
        page: Annotated[
            int,
            Query(ge=1, description="Page number"),
        ] = 1,
        limit: Annotated[
            int,
            Query(ge=1, le=200, description="Maximum results per page"),
        ] = 50,
        db: AsyncSession = Depends(get_db),
    ) -> ChatSessionListResponse:
        """Return chat sessions where current user is creator or participant."""
        return await list_chat_sessions(
            db=db, current_user=token_data, nano_id=nano_id, page=page, limit=limit
        )

    # ------------------------------------------------------------------
    # Message endpoints (Issue #101 – Sprint 7 Story 5.2)
    # ------------------------------------------------------------------

    @router.post(
        "/{session_id}/messages",
        response_model=ChatMessageCreateResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Send a message in a chat session",
        responses={
            401: {"description": "Missing or invalid authentication token"},
            403: {"description": "User is not a participant of this session"},
            404: {"description": "Chat session not found"},
            422: {"description": "Invalid message content (empty or exceeds 1000 chars)"},
        },
    )
    async def create_message(
        session_id: UUID,
        payload: ChatMessageCreateRequest,
        token_data: Annotated[TokenData, Depends(chat_access_dependency)],
        db: AsyncSession = Depends(get_db),
    ) -> ChatMessageCreateResponse:
        """Send a new message to an existing chat session.

        Only the two participants (creator and non-creator) may send messages.
        """
        _enforce_chat_content_filter(payload.content)
        await _enforce_chat_message_rate_limit(str(token_data.user_id), session_id)

        return await send_message(
            db=db,
            session_id=session_id,
            payload=payload,
            current_user=token_data,
        )

    @router.get(
        "/{session_id}/messages",
        response_model=ChatMessageListResponse,
        summary="Poll for messages in a chat session",
        responses={
            401: {"description": "Missing or invalid authentication token"},
            403: {"description": "User is not a participant of this session"},
            404: {"description": "Chat session not found"},
        },
    )
    async def get_messages(
        session_id: UUID,
        token_data: Annotated[TokenData, Depends(chat_access_dependency)],
        since: Annotated[
            datetime | None,
            Query(description="Return only messages created after this UTC timestamp (ISO-8601)"),
        ] = None,
        page: Annotated[
            int,
            Query(ge=1, description="Page number"),
        ] = 1,
        limit: Annotated[
            int,
            Query(ge=1, le=200, description="Maximum results per page"),
        ] = 50,
        db: AsyncSession = Depends(get_db),
    ) -> ChatMessageListResponse:
        """Retrieve messages in a chat session in chronological order.

        Pass ``since`` (ISO-8601 timestamp) to implement polling: only messages
        created strictly after that timestamp are returned.
        """
        return await list_messages(
            db=db,
            session_id=session_id,
            current_user=token_data,
            since=since,
            page=page,
            limit=limit,
        )

    return router
