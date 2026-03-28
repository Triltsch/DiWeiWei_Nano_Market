"""Business logic for chat session and message endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, ChatSession, Nano, NanoStatus
from app.modules.auth.tokens import TokenData
from app.modules.chat.schemas import (
    ChatMessageCreateRequest,
    ChatMessageCreateResponse,
    ChatMessageData,
    ChatMessageListMeta,
    ChatMessageListResponse,
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

    # Try to find an existing session for this nano
    # For participants: find where they are the participant
    # For creators: find where they are the creator
    if nano.creator_id == current_user.user_id:
        # Creator: look for sessions where they are the creator of this nano.
        # A creator can have multiple sessions for the same nano (unique constraint
        # is per nano + creator + participant). Use order_by + limit(1) to ensure
        # a deterministic single-row result and avoid MultipleResultsFound.
        session_query = (
            select(ChatSession)
            .where(
                and_(
                    ChatSession.nano_id == nano.id,
                    ChatSession.creator_id == current_user.user_id,
                )
            )
            .order_by(ChatSession.updated_at.desc())
            .limit(1)
        )
    else:
        # Participant: look for sessions where they are the participant
        session_query = select(ChatSession).where(
            and_(
                ChatSession.nano_id == nano.id,
                ChatSession.creator_id == nano.creator_id,
                ChatSession.participant_user_id == current_user.user_id,
            )
        )

    existing_session = (await db.execute(session_query)).scalar_one_or_none()

    # If no session exists and user is the creator, they cannot create a new one
    if existing_session is None and nano.creator_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creators cannot initiate a chat session with themselves",
        )

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


# ---------------------------------------------------------------------------
# Chat Message service (Issue #101 – Sprint 7 Story 5.2)
# ---------------------------------------------------------------------------


def _to_message_data(message: ChatMessage) -> ChatMessageData:
    """Convert ORM ChatMessage to API response schema."""
    return ChatMessageData(
        message_id=message.id,
        session_id=message.session_id,
        sender_id=message.sender_id,
        content=message.content,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


async def _get_session_or_403(
    *,
    db: AsyncSession,
    session_id: UUID,
    current_user_id: UUID,
) -> ChatSession:
    """Load chat session and verify caller is a participant.

    Raises 404 if the session does not exist, or 403 if the caller is not
    one of the two participants.
    """
    session = (
        await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if current_user_id not in {session.creator_id, session.participant_user_id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat session",
        )
    return session


async def send_message(
    *,
    db: AsyncSession,
    session_id: UUID,
    payload: ChatMessageCreateRequest,
    current_user: TokenData,
) -> ChatMessageCreateResponse:
    """Persist a new message in the given chat session and update last_message_at."""
    session = await _get_session_or_403(
        db=db,
        session_id=session_id,
        current_user_id=current_user.user_id,
    )

    message = ChatMessage(
        session_id=session.id,
        sender_id=current_user.user_id,
        content=payload.content,
    )
    db.add(message)

    try:
        await db.commit()
        await db.refresh(message)
    except IntegrityError as exc:
        # Roll back the failed transaction so the session can be reused safely.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not send message due to a database integrity error.",
        ) from exc
    except Exception as exc:
        # Ensure the session is rolled back on any unexpected error as well.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send message due to an unexpected error.",
        ) from exc

    # Use the DB-generated created_at so last_message_at is always in sync with
    # the actual message timestamp (avoids clock skew / commit latency drift).
    session.last_message_at = message.created_at
    await db.commit()

    now = datetime.now(timezone.utc)
    return ChatMessageCreateResponse(
        success=True,
        data=_to_message_data(message),
        timestamp=now,
    )


async def list_messages(
    *,
    db: AsyncSession,
    session_id: UUID,
    current_user: TokenData,
    since: datetime | None = None,
    page: int = 1,
    limit: int = 50,
) -> ChatMessageListResponse:
    """Return messages in a chat session in chronological order.

    The ``since`` parameter enables polling: passing the ``created_at`` of the
    last received message returns only newer messages.
    """
    await _get_session_or_403(
        db=db,
        session_id=session_id,
        current_user_id=current_user.user_id,
    )

    filters = [ChatMessage.session_id == session_id]
    if since is not None:
        filters.append(ChatMessage.created_at > since)

    count_query = select(func.count()).select_from(
        select(ChatMessage.id).where(and_(*filters)).subquery()
    )
    total_results = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * limit
    query = (
        select(ChatMessage)
        .where(and_(*filters))
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .offset(offset)
        .limit(limit)
    )

    rows = (await db.execute(query)).scalars().all()
    total_pages = (total_results + limit - 1) // limit if limit > 0 else 1
    now = datetime.now(timezone.utc)
    return ChatMessageListResponse(
        success=True,
        data=[_to_message_data(msg) for msg in rows],
        meta=ChatMessageListMeta(
            total_results=total_results,
            since_filter_applied=since is not None,
            current_page=page,
            page_size=limit,
            total_pages=total_pages,
            has_next_page=page < total_pages,
            has_prev_page=page > 1,
        ),
        timestamp=now,
    )
