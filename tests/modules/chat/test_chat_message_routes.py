"""Tests for chat message API routes (Sprint #7, Story 5.2 – Issue #101).

Scope:
- POST /api/v1/chats/{session_id}/messages – sending messages
- GET  /api/v1/chats/{session_id}/messages – polling for messages

Covers: authentication, participant authorization, input validation (empty /
over-length content), chronological ordering, since-based polling filter, and
pagination metadata.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models import (
    ChatMessage,
    ChatSession,
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoFormat,
    NanoStatus,
)
from app.modules.auth.tokens import create_access_token


class TestChatMessageRoutes:
    """Integration tests for send-message and poll-messages endpoints."""

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _create_user(db_session, email: str, username: str, role: str = "creator"):
        """Create and flush a minimal active user."""
        from app.models import User, UserRole, UserStatus

        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password_hash="dummy_hash",
            email_verified=True,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
            preferred_language="de",
            login_attempts=0,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @staticmethod
    async def _create_published_nano(db_session, creator_id: uuid.UUID) -> Nano:
        """Create and flush a published Nano owned by creator_id."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator_id,
            title="Message Test Nano",
            description="Nano for chat message tests",
            duration_minutes=10,
            competency_level=CompetencyLevel.BASIC,
            language="de",
            format=NanoFormat.TEXT,
            status=NanoStatus.PUBLISHED,
            version="1.0.0",
            license=LicenseType.CC_BY,
        )
        db_session.add(nano)
        await db_session.flush()
        return nano

    @staticmethod
    async def _create_session(
        db_session, nano_id: uuid.UUID, creator_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ChatSession:
        """Create and flush a chat session between creator and participant."""
        session = ChatSession(
            id=uuid.uuid4(),
            nano_id=nano_id,
            creator_id=creator_id,
            participant_user_id=participant_id,
        )
        db_session.add(session)
        await db_session.flush()
        return session

    # ------------------------------------------------------------------
    # POST /api/v1/chats/{session_id}/messages
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_message_as_participant_returns_201(self, async_client, db_session):
        """
        Non-creator participant sends a message to a session they belong to.

        Expects: 201, success=True, message persisted with correct sender/content.
        """
        creator = await self._create_user(
            db_session, "msg-creator@example.com", "msg_creator", role="creator"
        )
        participant = await self._create_user(
            db_session, "msg-participant@example.com", "msg_participant", role="consumer"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "Hello from participant!"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["content"] == "Hello from participant!"
        assert payload["data"]["sender_id"] == str(participant.id)
        assert payload["data"]["session_id"] == str(session.id)

    @pytest.mark.asyncio
    async def test_send_message_as_creator_returns_201(self, async_client, db_session):
        """
        Nano creator sends a message in their own session.

        Expects: 201, correct sender_id.
        """
        creator = await self._create_user(
            db_session, "msg-creator2@example.com", "msg_creator2", role="creator"
        )
        participant = await self._create_user(
            db_session, "msg-participant2@example.com", "msg_participant2", role="consumer"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"content": "Hello from creator!"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["data"]["sender_id"] == str(creator.id)

    @pytest.mark.asyncio
    async def test_send_message_requires_authentication(self, async_client, db_session):
        """
        Unauthenticated POST to messages endpoint is rejected.

        Expects: 401.
        """
        creator = await self._create_user(
            db_session, "msg-noauth-creator@example.com", "msg_noauth_creator"
        )
        participant = await self._create_user(
            db_session, "msg-noauth-participant@example.com", "msg_noauth_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            json={"content": "Should fail"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_send_message_forbidden_for_non_participant(self, async_client, db_session):
        """
        A user who is not part of the session cannot send messages.

        Expects: 403.
        """
        creator = await self._create_user(
            db_session, "msg-403-creator@example.com", "msg_403_creator"
        )
        participant = await self._create_user(
            db_session, "msg-403-participant@example.com", "msg_403_participant"
        )
        outsider = await self._create_user(
            db_session, "msg-403-outsider@example.com", "msg_403_outsider"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        outsider_token, _ = create_access_token(outsider.id, outsider.email, role="creator")
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={"content": "I should not be here"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_message_returns_404_for_unknown_session(self, async_client, db_session):
        """
        Sending to a non-existent session_id returns 404.

        Expects: 404.
        """
        creator = await self._create_user(
            db_session, "msg-404-creator@example.com", "msg_404_creator"
        )
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        response = await async_client.post(
            f"/api/v1/chats/{uuid.uuid4()}/messages",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"content": "Session does not exist"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_rejects_empty_content(self, async_client, db_session):
        """
        Empty string content is rejected by Pydantic validation.

        Expects: 422.
        """
        creator = await self._create_user(
            db_session, "msg-empty-creator@example.com", "msg_empty_creator"
        )
        participant = await self._create_user(
            db_session, "msg-empty-participant@example.com", "msg_empty_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_rejects_content_over_1000_chars(self, async_client, db_session):
        """
        Content exceeding 1000 characters is rejected by Pydantic validation.

        Expects: 422.
        """
        creator = await self._create_user(
            db_session, "msg-long-creator@example.com", "msg_long_creator"
        )
        participant = await self._create_user(
            db_session, "msg-long-participant@example.com", "msg_long_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        # Exactly 1001 characters
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "x" * 1001},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_accepts_exactly_1000_chars(self, async_client, db_session):
        """
        Content of exactly 1000 characters is accepted as the maximum boundary.

        Expects: 201.
        """
        creator = await self._create_user(
            db_session, "msg-max-creator@example.com", "msg_max_creator"
        )
        participant = await self._create_user(
            db_session, "msg-max-participant@example.com", "msg_max_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "a" * 1000},
        )

        assert response.status_code == 201

    # ------------------------------------------------------------------
    # GET /api/v1/chats/{session_id}/messages
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_messages_returns_chronological_order(self, async_client, db_session):
        """
        Messages are returned in ascending chronological order (oldest first).

        Inserts two messages and verifies ordering by created_at in response.
        """
        creator = await self._create_user(
            db_session, "msg-list-creator@example.com", "msg_list_creator"
        )
        participant = await self._create_user(
            db_session, "msg-list-participant@example.com", "msg_list_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)

        # Insert two messages with explicit ordering support via different timestamps.
        t1 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 1, 1, 10, 0, 1, tzinfo=timezone.utc)
        msg1 = ChatMessage(
            session_id=session.id,
            sender_id=participant.id,
            content="First",
        )
        msg2 = ChatMessage(
            session_id=session.id,
            sender_id=creator.id,
            content="Second",
        )
        db_session.add(msg1)
        await db_session.flush()
        # Force distinct timestamps at DB level via explicit assignment
        msg1.created_at = t1
        db_session.add(msg2)
        await db_session.flush()
        msg2.created_at = t2
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["total_results"] == 2
        # Chronological: First before Second
        assert payload["data"][0]["content"] == "First"
        assert payload["data"][1]["content"] == "Second"

    @pytest.mark.asyncio
    async def test_list_messages_since_filter_returns_newer_messages_only(
        self, async_client, db_session
    ):
        """
        ?since= filter returns only messages strictly newer than the given timestamp.

        Creates two messages; the since cursor is set between them.
        Expects only the newer message and meta.since_filter_applied=True.
        """
        creator = await self._create_user(
            db_session, "msg-since-creator@example.com", "msg_since_creator"
        )
        participant = await self._create_user(
            db_session, "msg-since-participant@example.com", "msg_since_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)

        t1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 1, 1, 12, 0, 5, tzinfo=timezone.utc)
        msg1 = ChatMessage(session_id=session.id, sender_id=participant.id, content="Old message")
        msg2 = ChatMessage(session_id=session.id, sender_id=creator.id, content="New message")
        db_session.add(msg1)
        await db_session.flush()
        msg1.created_at = t1
        db_session.add(msg2)
        await db_session.flush()
        msg2.created_at = t2
        await db_session.commit()

        # Cursor is exactly t1 — only msg2 (created at t2) should be returned.
        # Use params dict so httpx properly URL-encodes the '+00:00' timezone
        # offset (a bare '+' in a query string is decoded as a space by servers).
        cursor = t1.isoformat()
        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            params={"since": cursor},
            headers={"Authorization": f"Bearer {participant_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["since_filter_applied"] is True
        assert payload["meta"]["total_results"] == 1
        assert payload["data"][0]["content"] == "New message"

    @pytest.mark.asyncio
    async def test_list_messages_requires_authentication(self, async_client, db_session):
        """
        Unauthenticated GET to messages endpoint is rejected.

        Expects: 401.
        """
        creator = await self._create_user(
            db_session, "msg-listauth-creator@example.com", "msg_listauth_creator"
        )
        participant = await self._create_user(
            db_session, "msg-listauth-participant@example.com", "msg_listauth_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/chats/{session.id}/messages")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_messages_forbidden_for_non_participant(self, async_client, db_session):
        """
        A user who is not a session participant cannot read messages.

        Expects: 403.
        """
        creator = await self._create_user(
            db_session, "msg-list403-creator@example.com", "msg_list403_creator"
        )
        participant = await self._create_user(
            db_session, "msg-list403-participant@example.com", "msg_list403_participant"
        )
        outsider = await self._create_user(
            db_session, "msg-list403-outsider@example.com", "msg_list403_outsider"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        outsider_token, _ = create_access_token(outsider.id, outsider.email, role="creator")
        response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_messages_empty_session_returns_empty_list(self, async_client, db_session):
        """
        A session with no messages returns an empty list with total_results=0.

        Expects: 200, data=[], meta.total_results=0.
        """
        creator = await self._create_user(
            db_session, "msg-empty-list-creator@example.com", "msg_empty_list_creator"
        )
        participant = await self._create_user(
            db_session, "msg-empty-list-participant@example.com", "msg_empty_list_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"] == []
        assert payload["meta"]["total_results"] == 0
        assert payload["meta"]["since_filter_applied"] is False

    @pytest.mark.asyncio
    async def test_send_message_updates_session_last_message_at(self, async_client, db_session):
        """
        Sending a message updates the session's last_message_at timestamp.

        Expects: session.last_message_at is not None after sending.
        """
        creator = await self._create_user(
            db_session, "msg-ts-creator@example.com", "msg_ts_creator"
        )
        participant = await self._create_user(
            db_session, "msg-ts-participant@example.com", "msg_ts_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        # last_message_at should be NULL initially
        assert session.last_message_at is None

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "Timestamp update test"},
        )
        assert response.status_code == 201

        # The test and API share the same AsyncSession (via override_get_db).
        # The service updated session.last_message_at through the shared identity
        # map, so the change is reflected on the existing Python object directly.
        assert session.last_message_at is not None

    @pytest.mark.asyncio
    async def test_list_messages_pagination_limits_results_and_sets_meta(
        self, async_client, db_session
    ):
        """
        Pagination via limit=1/page=1 and limit=1/page=2 returns one message
        each, and the meta correctly reflects has_next_page/has_prev_page.

        Creates 3 messages, then queries page 1 (limit=1) and page 2 (limit=1).
        Verifies: single-item results, page meta, and has_next/has_prev flags.
        """
        creator = await self._create_user(
            db_session, "msg-pg-creator@example.com", "msg_pg_creator"
        )
        participant = await self._create_user(
            db_session, "msg-pg-participant@example.com", "msg_pg_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)

        # Insert 3 messages with strictly ordered timestamps for stable sorting.
        t_base = datetime(2026, 2, 1, 8, 0, 0, tzinfo=timezone.utc)
        for i, content in enumerate(["Message A", "Message B", "Message C"]):
            msg = ChatMessage(session_id=session.id, sender_id=participant.id, content=content)
            db_session.add(msg)
            await db_session.flush()
            msg.created_at = t_base.replace(second=i)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )

        # Page 1 of 3 at limit=1 — first message only.
        resp1 = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            params={"page": 1, "limit": 1},
            headers={"Authorization": f"Bearer {participant_token}"},
        )
        assert resp1.status_code == 200
        p1 = resp1.json()
        assert len(p1["data"]) == 1
        assert p1["data"][0]["content"] == "Message A"
        assert p1["meta"]["current_page"] == 1
        assert p1["meta"]["page_size"] == 1
        assert p1["meta"]["total_results"] == 3
        assert p1["meta"]["total_pages"] == 3
        assert p1["meta"]["has_next_page"] is True
        assert p1["meta"]["has_prev_page"] is False

        # Page 2 of 3 at limit=1 — middle message only.
        resp2 = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            params={"page": 2, "limit": 1},
            headers={"Authorization": f"Bearer {participant_token}"},
        )
        assert resp2.status_code == 200
        p2 = resp2.json()
        assert len(p2["data"]) == 1
        assert p2["data"][0]["content"] == "Message B"
        assert p2["meta"]["current_page"] == 2
        assert p2["meta"]["has_next_page"] is True
        assert p2["meta"]["has_prev_page"] is True
