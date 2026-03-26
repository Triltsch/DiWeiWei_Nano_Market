"""Pydantic schemas for chat session and message endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    """Request payload to create or reuse a chat session for a Nano."""

    nano_id: UUID = Field(description="Nano identifier to open chat for")


class ChatSessionData(BaseModel):
    """Chat session data shared by create and list responses."""

    session_id: UUID = Field(description="Chat session identifier")
    nano_id: UUID = Field(description="Referenced Nano identifier")
    creator_id: UUID = Field(description="Nano creator user id")
    participant_user_id: UUID = Field(description="Non-creator participant user id")
    counterpart_user_id: UUID = Field(description="Other participant from caller perspective")
    created_at: datetime = Field(description="Session creation timestamp")
    updated_at: datetime = Field(description="Session update timestamp")
    last_message_at: datetime | None = Field(None, description="Last message timestamp if present")


class ChatSessionCreateResponse(BaseModel):
    """Response for create or reuse session endpoint."""

    success: bool = Field(description="Whether operation was successful")
    data: ChatSessionData = Field(description="Created or reused chat session")
    meta: dict[str, bool] = Field(description="Metadata including whether session already existed")
    timestamp: datetime = Field(description="Response timestamp")


class ChatSessionListMeta(BaseModel):
    """Metadata for session listing with pagination info."""

    total_results: int = Field(ge=0, description="Total number of matching sessions")
    nano_filter_applied: bool = Field(description="Whether nano_id filter was applied")
    current_page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Maximum results per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_prev_page: bool = Field(description="Whether a previous page exists")


class ChatSessionListResponse(BaseModel):
    """Response schema for list chat sessions endpoint."""

    success: bool = Field(description="Whether operation was successful")
    data: list[ChatSessionData] = Field(description="Sessions for current user")
    meta: ChatSessionListMeta = Field(description="Result metadata")
    timestamp: datetime = Field(description="Response timestamp")


# ---------------------------------------------------------------------------
# Chat Message schemas (Issue #101 – Sprint 7 Story 5.2)
# ---------------------------------------------------------------------------


class ChatMessageCreateRequest(BaseModel):
    """Request body for sending a message to a chat session."""

    content: str = Field(
        min_length=1,
        max_length=1000,
        description="Message text content (1–1000 characters)",
    )


class ChatMessageData(BaseModel):
    """Single message in the API response."""

    message_id: UUID = Field(description="Message identifier")
    session_id: UUID = Field(description="Chat session this message belongs to")
    sender_id: UUID = Field(description="User who sent the message")
    content: str = Field(description="Message text content")
    created_at: datetime = Field(description="When the message was sent")
    updated_at: datetime = Field(description="When the message was last updated")


class ChatMessageCreateResponse(BaseModel):
    """Response for a successfully sent message."""

    success: bool = Field(description="Whether the message was sent successfully")
    data: ChatMessageData = Field(description="The persisted message")
    timestamp: datetime = Field(description="Response timestamp")


class ChatMessageListMeta(BaseModel):
    """Pagination and filter metadata for the message list response."""

    total_results: int = Field(ge=0, description="Total number of matching messages")
    since_filter_applied: bool = Field(description="Whether since timestamp filter was applied")
    current_page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Maximum results per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_prev_page: bool = Field(description="Whether a previous page exists")


class ChatMessageListResponse(BaseModel):
    """Paginated message list for polling use-case."""

    success: bool = Field(description="Whether operation was successful")
    data: list[ChatMessageData] = Field(description="Messages in chronological order")
    meta: ChatMessageListMeta = Field(description="Pagination and filter metadata")
    timestamp: datetime = Field(description="Response timestamp")
