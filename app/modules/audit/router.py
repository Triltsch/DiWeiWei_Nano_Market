"""Audit logging API router"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditAction
from app.modules.audit.service import AuditLogger
from app.modules.auth.middleware import require_role
from app.schemas import AuditLogResponse, AuditLogsQueryResponse, SuspiciousActivityResponse


def get_audit_router() -> APIRouter:
    """Create and configure the audit router.

    Returns:
        APIRouter: Configured router for audit endpoints
    """
    router = APIRouter(
        prefix="/api/v1/admin",
        tags=["audit"],
        dependencies=[Depends(require_role("admin"))],
    )

    @router.get(
        "/audit-logs",
        response_model=AuditLogsQueryResponse,
        summary="Query audit logs",
        description="Get paginated audit logs with optional filtering by user, action, resource type, and date range.",
    )
    async def query_audit_logs(
        session: AsyncSession = Depends(get_db),
        user_id: Optional[UUID] = Query(
            None, description="Filter by user who performed the action"
        ),
        action: Optional[str] = Query(None, description="Filter by action type"),
        resource_type: Optional[str] = Query(None, description="Filter by resource type"),
        start_date: Optional[datetime] = Query(
            None, description="Filter logs after this date (ISO format)"
        ),
        end_date: Optional[datetime] = Query(
            None, description="Filter logs before this date (ISO format)"
        ),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
        offset: int = Query(0, ge=0, description="Number of logs to skip"),
    ) -> AuditLogsQueryResponse:
        """Query audit logs with filtering and pagination.

        Returns:
            AuditLogsQueryResponse: Paginated list of audit logs
        """
        # Convert action string to enum if provided
        action_enum = None
        if action:
            try:
                action_enum = AuditAction[action.upper()]
            except KeyError:
                # If invalid action, just ignore the filter
                action_enum = None

        logs, total = await AuditLogger.query_logs(
            session,
            user_id=user_id,
            action=action_enum,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        # Convert ORM models to schemas
        log_responses = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                metadata=log.event_data,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

        return AuditLogsQueryResponse(
            logs=log_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get(
        "/audit-logs/recent",
        response_model=list[AuditLogResponse],
        summary="Get recent audit logs",
        description="Get the most recent audit logs (default last 100)",
    )
    async def get_recent_audit_logs(
        session: AsyncSession = Depends(get_db),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    ) -> list[AuditLogResponse]:
        """Get the most recent audit logs.

        Returns:
            list[AuditLogResponse]: List of recent audit logs
        """
        logs = await AuditLogger.get_recent_logs(session, limit=limit)

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                metadata=log.event_data,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

    @router.get(
        "/audit-logs/suspicious/{user_id}",
        response_model=SuspiciousActivityResponse,
        summary="Detect suspicious activity",
        description="Detect suspicious activity patterns for a specific user (e.g., multiple failed logins)",
    )
    async def detect_suspicious_activity(
        user_id: UUID,
        session: AsyncSession = Depends(get_db),
        window_minutes: int = Query(60, ge=1, le=1440, description="Time window to analyze"),
        threshold: int = Query(
            5, ge=1, le=100, description="Number of failures to consider suspicious"
        ),
    ) -> SuspiciousActivityResponse:
        """Detect suspicious activity for a user.

        Returns:
            SuspiciousActivityResponse: Suspicious activity details
        """
        logs = await AuditLogger.get_suspicious_activity(
            session,
            user_id=user_id,
            window_minutes=window_minutes,
            threshold=threshold,
        )

        log_responses = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                metadata=log.event_data,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

        return SuspiciousActivityResponse(
            user_id=user_id,
            activity_count=len(log_responses),
            logs=log_responses,
            message=(
                f"{len(log_responses)} suspicious activities detected in the last {window_minutes} minutes"
            ),
        )

    return router
