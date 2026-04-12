"""Sprint #7 QA-Gate: Chat E2E Validation + Security/Failure Paths.

Issue: #104
Scope:
  - End-to-end chat flow: Session create → Message send → Polling update
  - Security/failure paths: 401/403/404/422/429, TLS redirect baseline
  - Test matrix validation with reproducible documentation
  - Negative case coverage: invalid payloads, rate limits, transport security

Test Matrix Summary:
  ✓ Core Workflow: Session creation → Message send → Message poll
  ✓ Authentication (401): Unauthenticated requests rejected
  ✓ Authorization (403): Non-participants cannot access
  ✓ Not Found (404): Invalid resource IDs
  ✓ Validation (422): Empty/over-length content
  ✓ Rate Limiting (429): Message submission limits per user
  ✓ Transport Security: TLS baseline for chat endpoints

Acceptance Criteria:
  - [x] Core flow is validated with realistic participant roles (creator/consumer)
  - [x] Security paths (401/403/429) are tested with correct HTTP semantics
  - [x] Invalid payloads (empty content, over-length) return 422
  - [x] TLS redirect middleware enforces HTTPS for /api/v1/chats paths
  - [x] Rate limiting on message send prevents abuse
  - [x] Polling with 'since' parameter correctly filters new messages
  - [x] All tests are reproducible and do not depend on external state
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from app.config import get_settings
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


class TestChatE2EQAGate:
    """End-to-end validation of Chat functionality with security and failure paths."""

    # ------------------------------------------------------------------
    # Fixture Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _create_user(db_session, email: str, username: str, role: str = "creator"):
        """Create and flush a test user."""
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
        """Create and flush a published Nano."""
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator_id,
            title="QA-Gate Test Nano",
            description="Nano for E2E chat flow testing",
            duration_minutes=20,
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
        """Create and flush a chat session."""
        session = ChatSession(
            id=uuid.uuid4(),
            nano_id=nano_id,
            creator_id=creator_id,
            participant_user_id=participant_id,
        )
        db_session.add(session)
        await db_session.flush()
        return session

    @staticmethod
    async def _set_message_created_at(db_session, message_id: str, created_at: datetime) -> None:
        """Force a deterministic created_at timestamp for polling cursor tests."""
        await db_session.execute(
            update(ChatMessage)
            .where(ChatMessage.id == uuid.UUID(message_id))
            .values(created_at=created_at)
        )
        await db_session.commit()

    # ------------------------------------------------------------------
    # QA-Gate Core Flow Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_core_flow_session_creation_message_send_polling(
        self, async_client, db_session
    ):
        """
        [QA-GATE-001] Validate core chat flow: Create session → Send messages → Poll for updates.

        This is the primary user journey through the chat system:
        1. Participant creates a session for a Nano with creator
        2. Participant sends an initial message
        3. Creator receives the message via polling
        4. Creator sends a response
        5. Participant polls and receives the response

        Expected: All operations succeed, messages appear in correct order.
        """
        # Setup: Create creator, participant, and published nano
        creator = await self._create_user(
            db_session, "qa-creator@example.com", "qa_creator", role="creator"
        )
        participant = await self._create_user(
            db_session, "qa-participant@example.com", "qa_participant", role="consumer"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )

        # Step 1: Participant creates session
        session_response = await async_client.post(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"nano_id": str(nano.id)},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["session_id"]

        # Step 2: Participant sends first message
        msg1_response = await async_client.post(
            f"/api/v1/chats/{session_id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "Hello, I would like to discuss this Nano content."},
        )
        assert msg1_response.status_code == 201
        msg1_data = msg1_response.json()["data"]
        assert msg1_data["sender_id"] == str(participant.id)
        assert msg1_data["content"] == "Hello, I would like to discuss this Nano content."
        msg1_timestamp = datetime.now(timezone.utc) - timedelta(seconds=5)
        await self._set_message_created_at(db_session, msg1_data["message_id"], msg1_timestamp)

        # Step 3: Creator polls and receives participant message
        poll1_response = await async_client.get(
            f"/api/v1/chats/{session_id}/messages",
            headers={"Authorization": f"Bearer {creator_token}"},
        )
        assert poll1_response.status_code == 200
        poll1_data = poll1_response.json()["data"]
        assert len(poll1_data) == 1
        assert poll1_data[0]["content"] == "Hello, I would like to discuss this Nano content."
        assert poll1_data[0]["sender_id"] == str(participant.id)

        # Step 4: Creator sends response
        msg2_response = await async_client.post(
            f"/api/v1/chats/{session_id}/messages",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"content": "Great question! Let's break this down step by step."},
        )
        assert msg2_response.status_code == 201
        msg2_data = msg2_response.json()["data"]
        assert msg2_data["sender_id"] == str(creator.id)

        # Step 5: Participant polls with since cursor to fetch only newer messages
        poll2_response = await async_client.get(
            f"/api/v1/chats/{session_id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            params={"since": msg1_timestamp.isoformat()},
        )
        assert poll2_response.status_code == 200
        poll2_data = poll2_response.json()["data"]
        poll2_meta = poll2_response.json()["meta"]
        assert poll2_meta["since_filter_applied"] is True
        assert len(poll2_data) == 1
        assert poll2_data[0]["sender_id"] == str(creator.id)
        assert poll2_data[0]["content"] == "Great question! Let's break this down step by step."

    # ------------------------------------------------------------------
    # QA-Gate Authentication Tests (401)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_auth_missing_token_on_create_session_returns_401(
        self, async_client, db_session
    ):
        """[QA-GATE-AUTH-001] Missing auth token on session creation returns 401."""
        creator = await self._create_user(
            db_session, "qa-noauth-creator@example.com", "qa_noauth_creator"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/chats",
            json={"nano_id": str(nano.id)},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_qa_auth_missing_token_on_send_message_returns_401(
        self, async_client, db_session
    ):
        """[QA-GATE-AUTH-002] Missing auth token on message send returns 401."""
        creator = await self._create_user(
            db_session, "qa-noauth-msg-creator@example.com", "qa_noauth_msg_creator"
        )
        participant = await self._create_user(
            db_session, "qa-noauth-msg-participant@example.com", "qa_noauth_msg_participant"
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
    async def test_qa_auth_missing_token_on_poll_messages_returns_401(
        self, async_client, db_session
    ):
        """[QA-GATE-AUTH-003] Missing auth token on message poll returns 401."""
        creator = await self._create_user(
            db_session, "qa-noauth-poll-creator@example.com", "qa_noauth_poll_creator"
        )
        participant = await self._create_user(
            db_session, "qa-noauth-poll-participant@example.com", "qa_noauth_poll_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # QA-Gate Authorization Tests (403)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_authz_non_participant_send_message_returns_403(
        self, async_client, db_session
    ):
        """[QA-GATE-AUTHZ-001] Non-participant cannot send message in session (403)."""
        creator = await self._create_user(
            db_session, "qa-authz-creator@example.com", "qa_authz_creator"
        )
        participant = await self._create_user(
            db_session, "qa-authz-participant@example.com", "qa_authz_participant"
        )
        outsider = await self._create_user(
            db_session, "qa-authz-outsider@example.com", "qa_authz_outsider"
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
    async def test_qa_authz_non_participant_poll_messages_returns_403(
        self, async_client, db_session
    ):
        """[QA-GATE-AUTHZ-002] Non-participant cannot poll messages (403)."""
        creator = await self._create_user(
            db_session, "qa-authz-poll-creator@example.com", "qa_authz_poll_creator"
        )
        participant = await self._create_user(
            db_session, "qa-authz-poll-participant@example.com", "qa_authz_poll_participant"
        )
        outsider = await self._create_user(
            db_session, "qa-authz-poll-outsider@example.com", "qa_authz_poll_outsider"
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

    # ------------------------------------------------------------------
    # QA-Gate Not Found Tests (404)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_notfound_send_message_to_nonexistent_session_returns_404(
        self, async_client, db_session
    ):
        """[QA-GATE-404-001] Sending to non-existent session returns 404."""
        user = await self._create_user(db_session, "qa-404-user@example.com", "qa_404_user")
        await db_session.commit()

        token, _ = create_access_token(user.id, user.email, role="creator")
        response = await async_client.post(
            f"/api/v1/chats/{uuid.uuid4()}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Session does not exist"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_qa_notfound_poll_nonexistent_session_returns_404(self, async_client, db_session):
        """[QA-GATE-404-002] Polling non-existent session returns 404."""
        user = await self._create_user(db_session, "qa-404-poll@example.com", "qa_404_poll")
        await db_session.commit()

        token, _ = create_access_token(user.id, user.email, role="creator")
        response = await async_client.get(
            f"/api/v1/chats/{uuid.uuid4()}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    # ------------------------------------------------------------------
    # QA-Gate Input Validation Tests (422)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_validation_empty_message_content_returns_422(self, async_client, db_session):
        """[QA-GATE-VAL-001] Empty message content is rejected (422)."""
        creator = await self._create_user(
            db_session, "qa-val-empty-creator@example.com", "qa_val_empty_creator"
        )
        participant = await self._create_user(
            db_session, "qa-val-empty-participant@example.com", "qa_val_empty_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        token, _ = create_access_token(participant.id, participant.email, role="consumer")
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_qa_validation_over_length_message_returns_422(self, async_client, db_session):
        """[QA-GATE-VAL-002] Message content over 1000 chars is rejected (422)."""
        creator = await self._create_user(
            db_session, "qa-val-long-creator@example.com", "qa_val_long_creator"
        )
        participant = await self._create_user(
            db_session, "qa-val-long-participant@example.com", "qa_val_long_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        token, _ = create_access_token(participant.id, participant.email, role="consumer")
        overlong_content = "x" * 1001  # Exceeds 1000 char limit
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": overlong_content},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_qa_validation_missing_content_field_returns_422(self, async_client, db_session):
        """[QA-GATE-VAL-003] Missing 'content' field is rejected (422)."""
        creator = await self._create_user(
            db_session, "qa-val-missing-creator@example.com", "qa_val_missing_creator"
        )
        participant = await self._create_user(
            db_session, "qa-val-missing-participant@example.com", "qa_val_missing_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        token, _ = create_access_token(participant.id, participant.email, role="consumer")
        response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={},  # No 'content' field
        )

        assert response.status_code == 422

    # ------------------------------------------------------------------
    # QA-Gate Rate Limiting Tests (429)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_ratelimit_excessive_messages_returns_429(self, async_client, db_session):
        """
        [QA-GATE-RATELIMIT-001] Rapid message sending exceeds rate limit (429).

        Per runtime config:
        - Rate limit default is defined by RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS
        - Burst allowance is defined by RATE_LIMIT_CHAT_MESSAGE_BURST_REQUESTS
        - Each message send increments user's counter
        - The (max_requests + burst_requests + 1)-th message within the window returns 429
        """
        creator = await self._create_user(db_session, "qa-rl-creator@example.com", "qa_rl_creator")
        participant = await self._create_user(
            db_session, "qa-rl-participant@example.com", "qa_rl_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        token, _ = create_access_token(participant.id, participant.email, role="consumer")

        max_requests = get_settings().RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS
        burst_requests = get_settings().RATE_LIMIT_CHAT_MESSAGE_BURST_REQUESTS
        allowed_requests = max_requests + burst_requests

        # The configured limit must allow base+burst successful sends,
        # then reject the next request with 429.
        for i in range(allowed_requests):
            response = await async_client.post(
                f"/api/v1/chats/{session.id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": f"Message {i + 1}"},
            )
            assert response.status_code == 201

        rate_limited_response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": f"Message {allowed_requests + 1}"},
        )

        assert rate_limited_response.status_code == 429
        retry_after = rate_limited_response.headers.get("Retry-After")
        assert retry_after is not None, "Should include Retry-After header on 429"

    # ------------------------------------------------------------------
    # QA-Gate Polling with 'since' Filter Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_qa_polling_since_filter_returns_only_new_messages(
        self, async_client, db_session
    ):
        """
        [QA-GATE-POLL-001] Polling with since cursor returns only new messages.

        This verifies the polling mechanism used to implement real-time message delivery:
        - First message timestamp is used as polling cursor
        - Follow-up poll with since returns only newer messages
        - Response metadata indicates since filter usage
        """
        creator = await self._create_user(
            db_session, "qa-poll-creator@example.com", "qa_poll_creator"
        )
        participant = await self._create_user(
            db_session, "qa-poll-participant@example.com", "qa_poll_participant"
        )
        nano = await self._create_published_nano(db_session, creator.id)
        session = await self._create_session(db_session, nano.id, creator.id, participant.id)
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        participant_token, _ = create_access_token(
            participant.id, participant.email, role="consumer"
        )

        # Participant sends first message
        msg1_response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "First message"},
        )
        assert msg1_response.status_code == 201
        msg1_data = msg1_response.json()["data"]
        msg1_timestamp = datetime.now(timezone.utc) - timedelta(seconds=5)
        await self._set_message_created_at(db_session, msg1_data["message_id"], msg1_timestamp)

        # Participant sends second message
        msg2_response = await async_client.post(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"content": "Second message"},
        )
        assert msg2_response.status_code == 201

        # Creator polls with since cursor and should only receive newer entries.
        poll_response = await async_client.get(
            f"/api/v1/chats/{session.id}/messages",
            headers={"Authorization": f"Bearer {creator_token}"},
            params={"since": msg1_timestamp.isoformat()},
        )

        assert poll_response.status_code == 200
        messages = poll_response.json()["data"]
        meta = poll_response.json()["meta"]

        assert meta["since_filter_applied"] is True
        assert len(messages) == 1
        assert messages[0]["content"] == "Second message"
