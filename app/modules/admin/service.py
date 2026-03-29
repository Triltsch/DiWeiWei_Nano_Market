"""Admin service helpers for user management operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserStatus


class AdminUserManagementError(Exception):
    """Base exception for admin user-management flows."""


class AdminUserNotFoundError(AdminUserManagementError):
    """Raised when the addressed user does not exist."""


class AdminRoleChangeError(AdminUserManagementError):
    """Raised when a role change is not allowed."""


async def list_admin_users(
    db: AsyncSession,
    *,
    search: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[User], int]:
    """Return a filtered, paginated user list for the admin panel."""
    filters = []

    if search:
        normalized_search = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(User.email).like(normalized_search),
                func.lower(User.username).like(normalized_search),
                func.lower(func.coalesce(User.first_name, "")).like(normalized_search),
                func.lower(func.coalesce(User.last_name, "")).like(normalized_search),
            )
        )

    if role is not None:
        filters.append(User.role == role)

    if status is not None:
        filters.append(User.status == status)

    count_query = select(func.count()).select_from(User)
    if filters:
        count_query = count_query.where(*filters)
    total = (await db.execute(count_query)).scalar() or 0

    query = (
        select(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    if filters:
        query = query.where(*filters)

    users = (await db.execute(query)).scalars().all()
    return users, total


async def update_admin_user_role(
    db: AsyncSession,
    *,
    target_user_id: UUID,
    new_role: UserRole,
    actor_user_id: UUID,
) -> tuple[User, UserRole, bool]:
    """Update a user's role and return the updated user plus mutation metadata."""
    user = (await db.execute(select(User).where(User.id == target_user_id))).scalar_one_or_none()

    if user is None:
        raise AdminUserNotFoundError(f"User {target_user_id} not found")

    if user.id == actor_user_id:
        raise AdminRoleChangeError("Admins cannot change their own role")

    previous_role = user.role
    if previous_role == new_role:
        await db.refresh(user)
        return user, previous_role, False

    user.role = new_role
    db.add(user)
    # Flush only - the router commits once after the audit log is also written,
    # ensuring the role change and its audit entry are persisted atomically.
    await db.flush()
    await db.refresh(user)
    return user, previous_role, True
