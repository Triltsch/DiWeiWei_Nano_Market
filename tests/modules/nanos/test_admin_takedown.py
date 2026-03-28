"""
Admin takedown API tests (Sprint 8, Story 6.4).

Scope:
- Admin-only access control for takedown actions.
- Public visibility removal after takedown.
- Structured audit-trail capture (reason, actor context, timestamp metadata).
- Deterministic behavior when already removed content is processed again.
"""

import uuid
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    CompetencyLevel,
    LicenseType,
    Nano,
    NanoFormat,
    NanoStatus,
    User,
)
from app.modules.auth.service import verify_user_email


def _make_nano(*, creator_id: UUID, status: NanoStatus, title: str) -> Nano:
    """Build a Nano with complete metadata required by publication rules."""
    return Nano(
        id=uuid.uuid4(),
        creator_id=creator_id,
        title=title,
        description="Moderation-sensitive content for admin takedown tests.",
        duration_minutes=20,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="en",
        format=NanoFormat.VIDEO,
        status=status,
        version="1.0.0",
        license=LicenseType.CC_BY,
        file_storage_path="nanos/takedown-test.zip",
    )


async def _create_verified_user_with_token(async_client, db_session) -> tuple[User, str]:
    """Create a unique verified non-admin user and return (user, access_token)."""
    register_payload = {
        "email": f"takedown_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"takedown_{uuid.uuid4().hex[:8]}",
        "password": "SecurePassword123!",
        "accept_terms": True,
        "accept_privacy": True,
    }

    register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    user_id = UUID(register_response.json()["id"])

    await verify_user_email(db_session, user_id)

    user_stmt = select(User).where(User.id == user_id)
    user = (await db_session.execute(user_stmt)).scalar_one()

    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200

    return user, login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_takedown_requires_authentication(async_client, db_session, admin_user):
    """Requests without JWT must receive 401 and perform no mutation."""
    nano = _make_nano(
        creator_id=admin_user.id,
        status=NanoStatus.PUBLISHED,
        title="Unauthenticated Takedown Target",
    )
    db_session.add(nano)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": "Policy violation"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_takedown_forbids_non_admin(
    async_client,
    db_session,
):
    """Authenticated non-admin users must receive 403 Forbidden."""
    verified_user, access_token = await _create_verified_user_with_token(async_client, db_session)

    nano = _make_nano(
        creator_id=verified_user.id,
        status=NanoStatus.PUBLISHED,
        title="Forbidden Takedown Target",
    )
    db_session.add(nano)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": "Escalated legal complaint"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_takedown_archives_published_nano_blocks_public_and_logs_audit(
    async_client,
    db_session,
    admin_user,
    admin_token,
):
    """Published content must be removed from public flow and recorded in audit logs."""
    verified_user, _ = await _create_verified_user_with_token(async_client, db_session)

    nano = _make_nano(
        creator_id=verified_user.id,
        status=NanoStatus.PUBLISHED,
        title="Public Nano To Be Taken Down",
    )
    db_session.add(nano)
    await db_session.commit()

    reason = "Copyright complaint received"
    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": reason, "note": "DMCA ticket #4242"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["old_status"] == "published"
    assert payload["new_status"] == "archived"
    assert payload["already_removed"] is False
    assert payload["takedown_reason"] == reason

    await db_session.refresh(nano)
    assert nano.status == NanoStatus.ARCHIVED
    assert nano.archived_at is not None

    public_detail_response = await async_client.get(f"/api/v1/nanos/{nano.id}/detail")
    assert public_detail_response.status_code == 401

    audit_stmt = (
        select(AuditLog)
        .where(
            AuditLog.action == AuditAction.DATA_MODIFIED,
            AuditLog.resource_type == "nano",
            AuditLog.resource_id == str(nano.id),
        )
        .order_by(AuditLog.created_at.desc())
    )
    audit_log = (await db_session.execute(audit_stmt)).scalars().first()

    assert audit_log is not None
    assert audit_log.user_id == admin_user.id
    assert audit_log.event_data is not None
    assert audit_log.event_data.get("operation") == "admin_takedown"
    assert audit_log.event_data.get("takedown_reason") == reason
    assert audit_log.event_data.get("already_removed") is False
    assert audit_log.event_data.get("new_status") == "archived"
    assert audit_log.event_data.get("requested_at")


@pytest.mark.asyncio
async def test_admin_takedown_is_deterministic_for_already_removed_content(
    async_client,
    db_session,
    admin_token,
):
    """Repeated takedowns on non-public content should return a stable no-op result."""
    verified_user, _ = await _create_verified_user_with_token(async_client, db_session)

    nano = _make_nano(
        creator_id=verified_user.id,
        status=NanoStatus.ARCHIVED,
        title="Already Removed Nano",
    )
    db_session.add(nano)
    await db_session.commit()

    first = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": "Repeat operation test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    second = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": "Repeat operation test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["old_status"] == "archived"
    assert first_payload["new_status"] == "archived"
    assert first_payload["already_removed"] is True

    assert second_payload["old_status"] == "archived"
    assert second_payload["new_status"] == "archived"
    assert second_payload["already_removed"] is True
    assert first_payload["taken_down_at"] == second_payload["taken_down_at"]


@pytest.mark.asyncio
async def test_admin_takedown_rejects_whitespace_only_reason(
    async_client,
    db_session,
    admin_token,
):
    """Whitespace-only takedown reasons must be rejected with validation error."""
    verified_user, _ = await _create_verified_user_with_token(async_client, db_session)

    nano = _make_nano(
        creator_id=verified_user.id,
        status=NanoStatus.PUBLISHED,
        title="Whitespace Reason Validation Target",
    )
    db_session.add(nano)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/takedown",
        json={"reason": "   "},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422
