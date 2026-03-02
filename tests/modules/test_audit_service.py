"""Tests for audit logging service."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, User
from app.modules.audit.service import AuditLogger


class TestAuditLoggerService:
    """Test cases for the audit logging service."""

    @pytest.mark.asyncio
    async def test_log_action_creates_entry(
        self, db_session: AsyncSession, verified_user: User
    ) -> None:
        """Creates an audit entry with expected values."""
        log = await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=verified_user.id,
            resource_type="user",
            resource_id=str(verified_user.id),
            metadata={"email": verified_user.email},
            ip_address="192.168.1.10",
            user_agent="pytest-agent",
        )
        await db_session.commit()

        assert log.user_id == verified_user.id
        assert log.action == AuditAction.LOGIN_SUCCESS
        assert log.resource_type == "user"
        assert log.resource_id == str(verified_user.id)
        assert log.event_data == {"email": verified_user.email}
        assert log.ip_address == "192.168.1.10"
        assert log.user_agent == "pytest-agent"
        assert log.created_at is not None

    @pytest.mark.asyncio
    async def test_query_logs_filters_by_action(
        self, db_session: AsyncSession, verified_user: User
    ) -> None:
        """Returns only entries matching action filter."""
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

        logs, total = await AuditLogger.query_logs(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
        )

        assert total >= 1
        assert all(log.action == AuditAction.LOGIN_SUCCESS for log in logs)

    @pytest.mark.asyncio
    async def test_query_logs_applies_pagination(
        self, db_session: AsyncSession, verified_user: User
    ) -> None:
        """Supports limit/offset pagination for list views."""
        for _ in range(5):
            await AuditLogger.log_action(
                db_session,
                action=AuditAction.LOGIN_SUCCESS,
                user_id=verified_user.id,
                resource_type="user",
            )
        await db_session.commit()

        page_one, total = await AuditLogger.query_logs(db_session, limit=2, offset=0)
        page_two, _ = await AuditLogger.query_logs(db_session, limit=2, offset=2)

        assert len(page_one) == 2
        assert len(page_two) <= 2
        assert total >= 5
        if page_two:
            assert page_one[0].id != page_two[0].id

    @pytest.mark.asyncio
    async def test_get_suspicious_activity_threshold(
        self, db_session: AsyncSession, verified_user: User
    ) -> None:
        """Detects suspicious activity once threshold is reached."""
        for attempt in range(5):
            await AuditLogger.log_action(
                db_session,
                action=AuditAction.LOGIN_FAILURE,
                user_id=verified_user.id,
                resource_type="user_login_attempt",
                metadata={"attempt": attempt + 1},
            )
        await db_session.commit()

        suspicious_logs = await AuditLogger.get_suspicious_activity(
            db_session,
            user_id=verified_user.id,
            threshold=5,
            window_minutes=60,
        )

        assert len(suspicious_logs) == 5

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_deletes_entries(
        self, db_session: AsyncSession, verified_user: User
    ) -> None:
        """Removes logs older than retention window."""
        log = await AuditLogger.log_action(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=verified_user.id,
            resource_type="user",
        )
        log.created_at = datetime.now(timezone.utc) - timedelta(days=91)
        await db_session.commit()

        deleted_count = await AuditLogger.cleanup_old_logs(db_session, retention_days=90)
        await db_session.commit()

        assert deleted_count >= 1
