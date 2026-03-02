"""Audit logging service for tracking user actions and system events"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog


class AuditLogger:
    """Service for logging and querying audit events"""

    @staticmethod
    async def log_action(
        session: AsyncSession,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an audit event.

        Args:
            session: Database session
            action: Type of action performed
            user_id: User who performed the action (None for system events)
            resource_type: Type of resource affected (e.g. 'user', 'data')
            resource_id: ID of the resource affected
            metadata: Additional context about the action (sensitive data excluded)
            ip_address: IP address from which action originated
            user_agent: Browser user agent string

        Returns:
            AuditLog: The created audit log entry
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            event_data=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(audit_entry)
        await session.flush()
        return audit_entry

    @staticmethod
    async def query_logs(
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filtering options.

        Args:
            session: Database session
            user_id: Filter by user who performed the action
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter logs after this date (inclusive)
            end_date: Filter logs before this date (inclusive)
            limit: Maximum number of logs to return (max 1000)
            offset: Number of logs to skip

        Returns:
            Tuple of (logs, total_count)
        """
        # Build query filters
        filters = []

        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)

        if action is not None:
            filters.append(AuditLog.action == action)

        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)

        if start_date is not None:
            # Ensure timezone-aware datetime
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            filters.append(AuditLog.created_at >= start_date)

        if end_date is not None:
            # Ensure timezone-aware datetime
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            filters.append(AuditLog.created_at <= end_date)

        # Enforce limit cap for performance
        limit = min(limit, 1000)

        # Get total count for pagination
        count_query = select(func.count()).select_from(AuditLog)
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await session.execute(count_query)
        total_count = count_result.scalar() or 0

        # Get paginated results
        query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)

        if filters:
            query = query.where(and_(*filters))

        result = await session.execute(query)
        logs = result.scalars().all()

        return logs, total_count

    @staticmethod
    async def get_recent_logs(
        session: AsyncSession,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get the most recent audit logs.

        Args:
            session: Database session
            limit: Maximum number of logs to return

        Returns:
            List of recent audit logs
        """
        limit = min(limit, 1000)
        query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        retention_days: int = 90,
    ) -> int:
        """Delete audit logs older than the retention period.

        Args:
            session: Database session
            retention_days: Number of days to retain logs

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Use bulk DELETE to avoid loading rows into memory
        stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        result = await session.execute(stmt)
        await session.flush()

        return result.rowcount if result.rowcount else 0

    @staticmethod
    async def get_suspicious_activity(
        session: AsyncSession,
        user_id: UUID,
        window_minutes: int = 60,
        threshold: int = 5,
    ) -> list[AuditLog]:
        """Find suspicious activity patterns for a user.

        Detects multiple failed login attempts within a time window.

        Args:
            session: Database session
            user_id: User ID to check
            window_minutes: Time window to analyze
            threshold: Number of failures to consider suspicious

        Returns:
            List of suspicious activity logs
        """
        window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action == AuditAction.LOGIN_FAILURE,
                    AuditLog.created_at >= window_start,
                )
            )
            .order_by(desc(AuditLog.created_at))
        )

        result = await session.execute(query)
        suspicious_logs = result.scalars().all()

        return suspicious_logs if len(suspicious_logs) >= threshold else []
