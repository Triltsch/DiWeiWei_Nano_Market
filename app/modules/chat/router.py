"""Router for chat session endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.middleware import (
    ROLE_ADMIN,
    ROLE_CONSUMER,
    ROLE_CREATOR,
    ROLE_MODERATOR,
    require_any_role,
)
from app.modules.auth.tokens import TokenData
from app.modules.chat.schemas import (
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
    ChatSessionListResponse,
)
from app.modules.chat.service import create_or_get_chat_session, list_chat_sessions


def get_chat_router(prefix: str = "/api/v1/chats", tags: list[str] | None = None) -> APIRouter:
    """Create and configure router for chat session endpoints."""
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

    return router
