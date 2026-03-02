"""Tests for audit logging API routes."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, User
from app.modules.audit.service import AuditLogger


class TestAuditRoutes:
    """API tests for admin audit endpoints."""

    @pytest.mark.asyncio
    async def test_query_audit_logs_requires_admin_auth(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
    ) -> None:
        """Rejects unauthenticated and non-admin requests."""
        # Unauthenticated request
        response = await async_client.get("/api/v1/admin/audit-logs")
        assert response.status_code == 401

        # Regular user (non-admin) request
        # Login as regular user to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": verified_user.email, "password": "SecurePassword123!"},
        )
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/admin/audit-logs",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_query_audit_logs_returns_paginated_result(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
        admin_token: str,
    ) -> None:
        """Returns the expected pagination wrapper with logs."""
        await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=verified_user.id,
            resource_type="user",
            metadata={"email": verified_user.email},
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/admin/audit-logs?limit=10&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert isinstance(data["logs"], list)

    @pytest.mark.asyncio
    async def test_query_audit_logs_filters_by_action(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
        admin_token: str,
    ) -> None:
        """Applies action filter when provided."""
        await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=verified_user.id,
            resource_type="user",
        )
        await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGOUT,
            user_id=verified_user.id,
            resource_type="user",
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/admin/audit-logs?action=login_success",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        logs = response.json()["logs"]
        assert logs
        assert all(log["action"] == "login_success" for log in logs)

    @pytest.mark.asyncio
    async def test_recent_audit_logs_respects_limit(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
        admin_token: str,
    ) -> None:
        """Limits returned recent logs."""
        for _ in range(3):
            await AuditLogger.log_action(
                db_session,
                action=AuditAction.LOGIN_SUCCESS,
                user_id=verified_user.id,
                resource_type="user",
            )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/admin/audit-logs/recent?limit=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_suspicious_activity_endpoint_returns_payload(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
        admin_token: str,
    ) -> None:
        """Returns suspicious activity response for a user."""
        for _ in range(5):
            await AuditLogger.log_action(
                db_session,
                action=AuditAction.LOGIN_FAILURE,
                user_id=verified_user.id,
                resource_type="user_login_attempt",
            )
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/admin/audit-logs/suspicious/{verified_user.id}?window_minutes=60&threshold=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(verified_user.id)
        assert "activity_count" in data
        assert "logs" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_audit_log_response_contains_metadata_field(
        self,
        async_client,
        db_session: AsyncSession,
        verified_user: User,
        admin_token: str,
    ) -> None:
        """Exposes metadata in API response via schema alias."""
        await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=verified_user.id,
            resource_type="user",
            metadata={"source": "test"},
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/admin/audit-logs?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        logs = response.json()["logs"]
        assert logs
        assert "metadata" in logs[0]
