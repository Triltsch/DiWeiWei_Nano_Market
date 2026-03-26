"""Pydantic schemas for chat session endpoints."""

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
    """Metadata for session listing."""

    total: int = Field(ge=0, description="Number of sessions returned")
    nano_filter_applied: bool = Field(description="Whether nano_id filter was applied")


class ChatSessionListResponse(BaseModel):
    """Response schema for list chat sessions endpoint."""

    success: bool = Field(description="Whether operation was successful")
    data: list[ChatSessionData] = Field(description="Sessions for current user")
    meta: ChatSessionListMeta = Field(description="Result metadata")
    timestamp: datetime = Field(description="Response timestamp")
