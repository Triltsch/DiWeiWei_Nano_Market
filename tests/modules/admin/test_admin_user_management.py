"""Tests for admin-only user listing and role-management endpoints."""

from __future__ import annotations

import uuid
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import AuditAction, AuditLog, User, UserRole
from app.modules.auth.service import verify_user_email


async def _create_verified_user(async_client, db_session, *, prefix: str) -> User:
    safe_prefix = prefix[:8]
    unique_suffix = uuid.uuid4().hex[:8]
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{safe_prefix}_{unique_suffix}@example.com",
            "username": f"{safe_prefix}_{unique_suffix}",
            "password": "SecurePass123!",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])
    await verify_user_email(db_session, user_id)
    return (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()


class TestAdminUserManagement:
    """Coverage for the admin-panel user-management API."""

    @pytest.mark.asyncio
    async def test_user_list_requires_admin(self, async_client, access_token, admin_token) -> None:
        unauthenticated = await async_client.get("/api/v1/admin/users")
        assert unauthenticated.status_code == 401

        non_admin = await async_client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert non_admin.status_code == 403

        admin = await async_client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin.status_code == 200
        payload = admin.json()
        assert "users" in payload
        assert "total" in payload

    @pytest.mark.asyncio
    async def test_user_list_supports_search_and_role_filter(
        self,
        async_client,
        db_session,
        admin_token,
    ) -> None:
        creator = await _create_verified_user(async_client, db_session, prefix="creatorfilter")
        moderator = await _create_verified_user(async_client, db_session, prefix="moderatorfilter")
        moderator.role = UserRole.MODERATOR
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/admin/users?search=moderato&role=moderator&limit=10&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] >= 1
        assert len(payload["users"]) >= 1
        assert all(user["role"] == "moderator" for user in payload["users"])
        usernames = [user["username"] for user in payload["users"]]
        assert moderator.username in usernames
        assert creator.username not in usernames

    @pytest.mark.asyncio
    async def test_admin_can_change_user_role_and_audit_is_written(
        self,
        async_client,
        db_session,
        admin_user,
        admin_token,
    ) -> None:
        target = await _create_verified_user(async_client, db_session, prefix="rolechange")

        response = await async_client.patch(
            f"/api/v1/admin/users/{target.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["role"] == "moderator"

        await db_session.refresh(target)
        assert target.role == UserRole.MODERATOR

        audit_log = (
            (
                await db_session.execute(
                    select(AuditLog)
                    .where(
                        AuditLog.action == AuditAction.ROLE_CHANGED,
                        AuditLog.resource_id == str(target.id),
                    )
                    .order_by(AuditLog.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        assert audit_log is not None
        assert audit_log.user_id == admin_user.id
        assert audit_log.event_data is not None
        assert audit_log.event_data["old_role"] == "creator"
        assert audit_log.event_data["new_role"] == "moderator"

    @pytest.mark.asyncio
    async def test_admin_cannot_change_own_role(
        self, async_client, admin_user, admin_token
    ) -> None:
        response = await async_client.patch(
            f"/api/v1/admin/users/{admin_user.id}/role",
            json={"role": "creator"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Admins cannot change their own role"
