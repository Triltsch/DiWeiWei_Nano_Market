"""Admin service helpers for user management operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserStatus
from app.modules.auth.password import hash_password


class AdminUserManagementError(Exception):
    """Base exception for admin user-management flows."""


class AdminUserNotFoundError(AdminUserManagementError):
    """Raised when the addressed user does not exist."""


class AdminRoleChangeError(AdminUserManagementError):
    """Raised when a role change is not allowed."""


class AdminUserDeleteConflictError(AdminUserManagementError):
    """Raised when a user deletion request violates admin business rules."""


async def list_admin_users(
    db: AsyncSession,
    *,
    search: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    exclude_deleted: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[User], int]:
    """Return a filtered, paginated user list for the admin panel.

    Args:
        exclude_deleted: When True (default) and no explicit ``status`` filter is
            provided, soft-deleted users are omitted.  Set to False to include
            them in an unfiltered result set.  When ``status`` is passed
            explicitly this flag is ignored — the caller controls inclusion via
            the status filter.
    """
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
    elif exclude_deleted:
        # When no explicit status filter is provided, hide deleted users by default.
        # API consumers that want deleted users in an unfiltered result can pass
        # exclude_deleted=False; the router exposes this as an `exclude_deleted`
        # query parameter so the intent stays explicit for all callers.
        filters.append(User.status != UserStatus.DELETED)

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


async def delete_admin_user(
    db: AsyncSession,
    *,
    target_user_id: UUID,
    actor_user_id: UUID,
) -> tuple[User, str, str]:
    """Soft-delete a user account for admin workflows.

    The record remains in place for referential integrity, but identifying fields are
    anonymized so the original email/username can be re-used for new test registrations.
    """
    user = (await db.execute(select(User).where(User.id == target_user_id))).scalar_one_or_none()

    if user is None:
        raise AdminUserNotFoundError(f"User {target_user_id} not found")

    if user.id == actor_user_id:
        raise AdminUserDeleteConflictError("Admins cannot delete their own account")

    if user.status == UserStatus.DELETED:
        raise AdminUserDeleteConflictError("User is already deleted")

    previous_email = user.email
    previous_username = user.username

    anonymized_suffix = user.id.hex[:16]
    user.email = f"deleted+{user.id.hex}@example.com"
    user.username = f"del_{anonymized_suffix}"
    user.password_hash = hash_password(uuid4().hex)
    user.status = UserStatus.DELETED
    user.role = UserRole.CONSUMER
    user.email_verified = False
    user.verified_at = None
    user.last_login = None
    user.login_attempts = 0
    user.locked_until = None
    user.first_name = None
    user.last_name = None
    user.bio = None
    user.company = None
    user.job_title = None
    user.phone = None
    user.profile_avatar = None
    # Do NOT set deletion_requested_at / deletion_scheduled_at here.
    # Those fields drive the GDPR scheduled hard-deletion flow: setting them
    # to `now` would immediately qualify the record for permanent erasure by
    # cleanup jobs.  Admin soft-delete is a durable anonymisation — the row
    # stays for referential integrity and must not be swept by the GDPR purge.
    user.deletion_requested_at = None
    user.deletion_scheduled_at = None
    user.deletion_reason = "admin_deleted"

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user, previous_email, previous_username
