"""Business logic for chat session endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession, Nano, NanoStatus
from app.modules.auth.tokens import TokenData
from app.modules.chat.schemas import (
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
    ChatSessionData,
    ChatSessionListMeta,
    ChatSessionListResponse,
)


def _to_session_data(session: ChatSession, current_user_id: UUID) -> ChatSessionData:
    """Convert ORM chat session model to API response schema."""
    counterpart_user_id = (
        session.participant_user_id if session.creator_id == current_user_id else session.creator_id
    )
    return ChatSessionData(
        session_id=session.id,
        nano_id=session.nano_id,
        creator_id=session.creator_id,
        participant_user_id=session.participant_user_id,
        counterpart_user_id=counterpart_user_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
    )


async def create_or_get_chat_session(
    *,
    db: AsyncSession,
    payload: ChatSessionCreateRequest,
    current_user: TokenData,
) -> ChatSessionCreateResponse:
    """Create a new chat session or return an existing one for the same participants/nano."""
    nano_query = select(Nano).where(
        and_(Nano.id == payload.nano_id, Nano.status == NanoStatus.PUBLISHED)
    )
    nano = (await db.execute(nano_query)).scalar_one_or_none()
    if nano is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published Nano not found",
        )

    if nano.creator_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creators cannot open a chat with themselves",
        )

    session_query = select(ChatSession).where(
        and_(
            ChatSession.nano_id == nano.id,
            ChatSession.creator_id == nano.creator_id,
            ChatSession.participant_user_id == current_user.user_id,
        )
    )
    existing_session = (await db.execute(session_query)).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing_session is not None:
        return ChatSessionCreateResponse(
            success=True,
            data=_to_session_data(existing_session, current_user.user_id),
            meta={"reused": True},
            timestamp=now,
        )

    new_session = ChatSession(
        nano_id=nano.id,
        creator_id=nano.creator_id,
        participant_user_id=current_user.user_id,
    )
    db.add(new_session)
    try:
        await db.commit()
        await db.refresh(new_session)
    except IntegrityError:
        # Concurrent request already created the session; rollback and return the existing one.
        await db.rollback()
        race_session = (await db.execute(session_query)).scalar_one()
        return ChatSessionCreateResponse(
            success=True,
            data=_to_session_data(race_session, current_user.user_id),
            meta={"reused": True},
            timestamp=now,
        )

    return ChatSessionCreateResponse(
        success=True,
        data=_to_session_data(new_session, current_user.user_id),
        meta={"reused": False},
        timestamp=now,
    )


async def list_chat_sessions(
    *,
    db: AsyncSession,
    current_user: TokenData,
    nano_id: UUID | None = None,
    page: int = 1,
    limit: int = 50,
) -> ChatSessionListResponse:
    """List chat sessions where current user is one of the participants (paginated)."""
    filters = [
        or_(
            ChatSession.creator_id == current_user.user_id,
            ChatSession.participant_user_id == current_user.user_id,
        )
    ]
    if nano_id is not None:
        filters.append(ChatSession.nano_id == nano_id)

    count_query = select(func.count()).select_from(
        select(ChatSession.id).where(and_(*filters)).subquery()
    )
    total_results = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * limit
    query = (
        select(ChatSession)
        .where(and_(*filters))
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    rows = (await db.execute(query)).scalars().all()
    total_pages = (total_results + limit - 1) // limit if limit > 0 else 1
    now = datetime.now(timezone.utc)
    return ChatSessionListResponse(
        success=True,
        data=[_to_session_data(session, current_user.user_id) for session in rows],
        meta=ChatSessionListMeta(
            total_results=total_results,
            nano_filter_applied=nano_id is not None,
            current_page=page,
            page_size=limit,
            total_pages=total_pages,
            has_next_page=page < total_pages,
            has_prev_page=page > 1,
        ),
        timestamp=now,
    )
