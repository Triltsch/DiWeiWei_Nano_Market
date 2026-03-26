"""Tests for chat session API routes (Sprint #7, Story 5.1)."""

import uuid

import pytest

from app.models import ChatSession, CompetencyLevel, LicenseType, Nano, NanoFormat, NanoStatus
from app.modules.auth.tokens import create_access_token


class TestChatSessionRoutes:
    """Integration tests for create/list chat session endpoints."""

    @staticmethod
    async def _create_user(db_session, email: str, username: str, role: str = "creator"):
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
    async def _create_published_nano(db_session, creator_id):
        nano = Nano(
            id=uuid.uuid4(),
            creator_id=creator_id,
            title="Chat-ready Nano",
            description="Nano for chat session tests",
            duration_minutes=25,
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

    @pytest.mark.asyncio
    async def test_create_chat_session_creates_and_reuses_existing_session(
        self, async_client, db_session
    ):
        """Creating chat for same nano and participants reuses existing session."""
        creator = await self._create_user(
            db_session,
            "chat-creator@example.com",
            "chat_creator",
            role="creator",
        )
        participant = await self._create_user(
            db_session,
            "chat-participant@example.com",
            "chat_participant",
            role="creator",
        )
        nano = await self._create_published_nano(db_session, creator.id)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id,
            participant.email,
            role="creator",
        )

        first_response = await async_client.post(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"nano_id": str(nano.id)},
        )
        second_response = await async_client.post(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {participant_token}"},
            json={"nano_id": str(nano.id)},
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 200

        first_payload = first_response.json()
        second_payload = second_response.json()

        assert first_payload["success"] is True
        assert first_payload["meta"]["reused"] is False
        assert second_payload["meta"]["reused"] is True
        assert first_payload["data"]["session_id"] == second_payload["data"]["session_id"]

        all_sessions = (await db_session.execute(ChatSession.__table__.select())).all()
        assert len(all_sessions) == 1

    @pytest.mark.asyncio
    async def test_create_chat_session_requires_authentication(self, async_client, db_session):
        """Unauthenticated requests are rejected with 401."""
        creator = await self._create_user(
            db_session,
            "chat-auth-creator@example.com",
            "chat_auth_creator",
            role="creator",
        )
        nano = await self._create_published_nano(db_session, creator.id)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/chats",
            json={"nano_id": str(nano.id)},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_chat_session_forbids_creator_chat_with_self(
        self, async_client, db_session
    ):
        """Creator cannot create a session with themselves on their own Nano."""
        creator = await self._create_user(
            db_session,
            "chat-self-creator@example.com",
            "chat_self_creator",
            role="creator",
        )
        nano = await self._create_published_nano(db_session, creator.id)
        await db_session.commit()

        creator_token, _ = create_access_token(creator.id, creator.email, role="creator")
        response = await async_client.post(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"nano_id": str(nano.id)},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_chat_sessions_returns_only_current_user_sessions(
        self, async_client, db_session
    ):
        """List endpoint returns only sessions where current user is a participant."""
        creator = await self._create_user(
            db_session,
            "chat-list-creator@example.com",
            "chat_list_creator",
            role="creator",
        )
        participant = await self._create_user(
            db_session,
            "chat-list-participant@example.com",
            "chat_list_participant",
            role="creator",
        )
        other_user = await self._create_user(
            db_session,
            "chat-list-other@example.com",
            "chat_list_other",
            role="creator",
        )

        nano_for_participant = await self._create_published_nano(db_session, creator.id)
        nano_for_other = await self._create_published_nano(db_session, creator.id)

        session_for_participant = ChatSession(
            nano_id=nano_for_participant.id,
            creator_id=creator.id,
            participant_user_id=participant.id,
        )
        session_for_other = ChatSession(
            nano_id=nano_for_other.id,
            creator_id=creator.id,
            participant_user_id=other_user.id,
        )
        db_session.add(session_for_participant)
        db_session.add(session_for_other)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id,
            participant.email,
            role="creator",
        )

        response = await async_client.get(
            "/api/v1/chats",
            headers={"Authorization": f"Bearer {participant_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["total_results"] == 1
        assert payload["data"][0]["session_id"] == str(session_for_participant.id)
        assert payload["data"][0]["counterpart_user_id"] == str(creator.id)

    @pytest.mark.asyncio
    async def test_list_chat_sessions_filters_by_nano_id(self, async_client, db_session):
        """
        GET /api/v1/chats?nano_id=... returns only sessions for the given Nano.

        Creates two sessions for the same participant across two different Nanos, then
        queries with nano_id filter.  Expects exactly one result and meta.nano_filter_applied=True.
        """
        creator = await self._create_user(
            db_session,
            "chat-nanofilter-creator@example.com",
            "chat_nanofilter_creator",
            role="creator",
        )
        participant = await self._create_user(
            db_session,
            "chat-nanofilter-participant@example.com",
            "chat_nanofilter_participant",
            role="creator",
        )

        nano_a = await self._create_published_nano(db_session, creator.id)
        nano_b = await self._create_published_nano(db_session, creator.id)

        session_a = ChatSession(
            nano_id=nano_a.id,
            creator_id=creator.id,
            participant_user_id=participant.id,
        )
        session_b = ChatSession(
            nano_id=nano_b.id,
            creator_id=creator.id,
            participant_user_id=participant.id,
        )
        db_session.add(session_a)
        db_session.add(session_b)
        await db_session.commit()

        participant_token, _ = create_access_token(
            participant.id,
            participant.email,
            role="creator",
        )

        # Query with nano_id filter — should return only session_a.
        response = await async_client.get(
            f"/api/v1/chats?nano_id={nano_a.id}",
            headers={"Authorization": f"Bearer {participant_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["total_results"] == 1
        assert payload["meta"]["nano_filter_applied"] is True
        assert payload["data"][0]["session_id"] == str(session_a.id)
