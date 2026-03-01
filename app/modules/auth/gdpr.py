"""GDPR/DSGVO compliance service - data export and account deletion"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConsentAudit, User, UserStatus
from app.schemas import AccountDeletionResponse, ConsentResponse, UserDataExport


class GDPRError(Exception):
    """Base GDPR operation error"""

    pass


class AccountAlreadyScheduledForDeletionError(GDPRError):
    """Account is already scheduled for deletion"""

    pass


async def export_user_data(db_session: AsyncSession, user_id: UUID) -> UserDataExport:
    """
    Export all user data in machine-readable format for GDPR compliance.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        UserDataExport: Complete user data export

    Raises:
        GDPRError: If user not found
    """
    # Fetch user
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise GDPRError("User not found")

    # Create export data
    export_data = UserDataExport(
        user_id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        company=user.company,
        job_title=user.job_title,
        phone=user.phone,
        preferred_language=user.preferred_language,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        email_verified=user.email_verified,
        verified_at=user.verified_at,
        status=user.status.value,
        role=user.role.value,
        accepted_terms=user.accepted_terms,
        accepted_privacy=user.accepted_privacy,
    )

    return export_data


async def request_account_deletion(
    db_session: AsyncSession, user_id: UUID, reason: Optional[str] = None
) -> AccountDeletionResponse:
    """
    Request account deletion with 30-day grace period.

    Args:
        db_session: Database session
        user_id: User ID
        reason: Optional reason for deletion

    Returns:
        AccountDeletionResponse: Deletion confirmation with schedule

    Raises:
        GDPRError: If user not found
        AccountAlreadyScheduledForDeletionError: If already scheduled
    """
    # Fetch user
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise GDPRError("User not found")

    # Check if already scheduled
    if user.deletion_requested_at is not None:
        raise AccountAlreadyScheduledForDeletionError(
            f"Account deletion already scheduled for {user.deletion_scheduled_at.isoformat()}"
        )

    # Calculate deletion date (30 days from now)
    now = datetime.now(timezone.utc)
    grace_period_days = 30
    deletion_date = now + timedelta(days=grace_period_days)

    # Update user
    user.deletion_requested_at = now
    user.deletion_scheduled_at = deletion_date
    user.deletion_reason = reason
    user.status = UserStatus.INACTIVE  # Deactivate account immediately

    await db_session.commit()

    return AccountDeletionResponse(
        message=f"Account deletion scheduled. You have {grace_period_days} days to cancel.",
        deletion_scheduled_at=deletion_date,
        grace_period_days=grace_period_days,
    )


async def cancel_account_deletion(db_session: AsyncSession, user_id: UUID) -> None:
    """
    Cancel a pending account deletion request.

    Args:
        db_session: Database session
        user_id: User ID

    Raises:
        GDPRError: If user not found or no deletion pending
    """
    # Fetch user
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise GDPRError("User not found")

    if user.deletion_requested_at is None:
        raise GDPRError("No deletion request pending")

    if user.deletion_scheduled_at is None:
        raise GDPRError("No deletion request pending")

    now = datetime.now(timezone.utc)
    scheduled_at = user.deletion_scheduled_at
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    if now >= scheduled_at:
        raise GDPRError("Deletion grace period has expired and can no longer be cancelled")

    # Cancel deletion
    user.deletion_requested_at = None
    user.deletion_scheduled_at = None
    user.deletion_reason = None
    user.status = UserStatus.ACTIVE  # Reactivate account

    await db_session.commit()


async def execute_account_deletion(db_session: AsyncSession, user_id: UUID) -> None:
    """
    Permanently delete user account and all associated data.
    This should only be called after the grace period has expired.

    Args:
        db_session: Database session
        user_id: User ID

    Raises:
        GDPRError: If user not found or grace period not expired
    """
    # Fetch user
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise GDPRError("User not found")

    # Verify grace period has expired
    if user.deletion_scheduled_at is None:
        raise GDPRError("No deletion scheduled for this user")

    now = datetime.now(timezone.utc)
    # Handle timezone-naive datetimes from SQLite
    scheduled_at = user.deletion_scheduled_at
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    if now < scheduled_at:
        raise GDPRError(
            f"Grace period has not expired. Deletion scheduled for {scheduled_at.isoformat()}"
        )

    # Delete consent audit records
    await db_session.execute(ConsentAudit.__table__.delete().where(ConsentAudit.user_id == user_id))

    # Delete user (hard delete)
    await db_session.delete(user)
    await db_session.commit()


async def get_user_consents(db_session: AsyncSession, user_id: UUID) -> list[ConsentResponse]:
    """
    Get all consent records for a user.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        List of consent records

    Raises:
        GDPRError: If user not found
    """
    # Verify user exists
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise GDPRError("User not found")

    # Fetch all consent audit records for this user
    query = (
        select(ConsentAudit)
        .where(ConsentAudit.user_id == user_id)
        .order_by(ConsentAudit.timestamp.desc())
    )
    result = await db_session.execute(query)
    consents = result.scalars().all()

    # Convert to response format
    return [
        ConsentResponse(
            consent_type=consent.consent_type.value,
            accepted=consent.accepted,
            timestamp=consent.timestamp,
        )
        for consent in consents
    ]
