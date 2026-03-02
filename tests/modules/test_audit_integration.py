"""Integration tests for audit logging through auth endpoints."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog
from app.modules.auth.service import verify_user_email


async def _latest_log_for_action(db_session: AsyncSession, action: AuditAction) -> AuditLog | None:
    """Get newest log entry for a given action."""
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == action).order_by(AuditLog.created_at.desc())
    )
    return result.scalars().first()


class TestAuditLoggingIntegration:
    """Auth flow tests that assert audit events are persisted."""

    @pytest.mark.asyncio
    async def test_registration_is_logged(self, async_client, db_session: AsyncSession) -> None:
        """Stores USER_REGISTERED event with metadata."""
        email = f"audit_{uuid.uuid4().hex}@example.com"
        username = f"audit_{uuid.uuid4().hex[:12]}"

        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "SecurePass123!",
                "accept_terms": True,
                "accept_privacy": True,
            },
            headers={"User-Agent": "AuditIntegration/1.0"},
        )
        assert response.status_code == 201

        log = await _latest_log_for_action(db_session, AuditAction.USER_REGISTERED)
        assert log is not None
        assert log.event_data is not None
        assert log.event_data.get("email") == email
        assert log.event_data.get("username") == username

    @pytest.mark.asyncio
    async def test_login_success_is_logged(
        self,
        async_client,
        db_session: AsyncSession,
        test_user_data: dict,
    ) -> None:
        """Stores LOGIN_SUCCESS after verified login."""
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        from uuid import UUID

        await verify_user_email(db_session, UUID(user_id))

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
            headers={"User-Agent": "AuditLogin/1.0", "X-Forwarded-For": "203.0.113.10"},
        )
        assert login_response.status_code == 200

        log = await _latest_log_for_action(db_session, AuditAction.LOGIN_SUCCESS)
        assert log is not None
        assert log.user_agent == "AuditLogin/1.0"
        assert log.ip_address == "203.0.113.10"

    @pytest.mark.asyncio
    async def test_login_failure_is_logged(
        self,
        async_client,
        db_session: AsyncSession,
        test_user_data: dict,
    ) -> None:
        """Stores LOGIN_FAILURE for invalid credentials."""
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": "WrongPassword123!"},
        )
        assert login_response.status_code in (401, 403)

        log = await _latest_log_for_action(db_session, AuditAction.LOGIN_FAILURE)
        assert log is not None
        assert log.event_data is not None
        assert log.event_data.get("email") == test_user_data["email"].lower()

    @pytest.mark.asyncio
    async def test_email_verification_and_refresh_are_logged(
        self,
        async_client,
        db_session: AsyncSession,
    ) -> None:
        """Stores EMAIL_VERIFIED and TOKEN_REFRESH for successful flows."""
        email = f"verify_{uuid.uuid4().hex}@example.com"
        username = f"verify_{uuid.uuid4().hex[:12]}"
        password = "SecurePass123!"

        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "accept_terms": True,
                "accept_privacy": True,
            },
        )
        assert register_response.status_code == 201

        resend_response = await async_client.post(
            "/api/v1/auth/resend-verification-email",
            json={"email": email},
        )
        assert resend_response.status_code == 200
        message = resend_response.json()["message"]
        token = message.split("Copy this token to verify your email: ", maxsplit=1)[1]

        verify_response = await async_client.post(
            "/api/v1/auth/verify-email",
            json={"token": token},
        )
        assert verify_response.status_code == 200

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = await async_client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200

        verified_log = await _latest_log_for_action(db_session, AuditAction.EMAIL_VERIFIED)
        refresh_log = await _latest_log_for_action(db_session, AuditAction.TOKEN_REFRESH)

        assert verified_log is not None
        assert refresh_log is not None

    @pytest.mark.asyncio
    async def test_logout_is_logged(
        self,
        async_client,
        db_session: AsyncSession,
    ) -> None:
        """Stores LOGOUT event for authenticated logout."""
        email = f"logout_{uuid.uuid4().hex}@example.com"
        username = f"logout_{uuid.uuid4().hex[:12]}"
        password = "SecurePass123!"

        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "accept_terms": True,
                "accept_privacy": True,
            },
        )
        assert register_response.status_code == 201

        resend_response = await async_client.post(
            "/api/v1/auth/resend-verification-email",
            json={"email": email},
        )
        token = resend_response.json()["message"].split(
            "Copy this token to verify your email: ", maxsplit=1
        )[1]
        verify_response = await async_client.post(
            "/api/v1/auth/verify-email", json={"token": token}
        )
        assert verify_response.status_code == 200

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200

        log = await _latest_log_for_action(db_session, AuditAction.LOGOUT)
        assert log is not None
