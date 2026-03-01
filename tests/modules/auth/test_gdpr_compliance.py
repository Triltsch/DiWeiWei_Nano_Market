"""
Test GDPR/DSGVO compliance features.

This module tests:
- Consent tracking during registration
- User data export endpoint
- Account deletion with grace period
- Deletion cancellation
- Consent history retrieval
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import ConsentAudit, ConsentType, User, UserStatus
from app.modules.auth.gdpr import (
    AccountAlreadyScheduledForDeletionError,
    GDPRError,
    cancel_account_deletion,
    execute_account_deletion,
    export_user_data,
    get_user_consents,
    request_account_deletion,
)
from app.modules.auth.service import register_user
from app.schemas import UserRegister


@pytest.mark.asyncio
class TestConsentTracking:
    """
    Test consent tracking during user registration.

    Verifies that:
    - User must accept terms and privacy policy to register
    - Consent timestamps are recorded correctly
    - Consent audit log entries are created
    """

    async def test_registration_requires_terms_acceptance(self, db_session):
        """Test that registration fails without Terms of Service acceptance"""
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=False,  # Not accepting terms
            accept_privacy=True,
        )

        with pytest.raises(Exception) as exc_info:
            await register_user(db_session, user_data)

        assert "Terms of Service" in str(exc_info.value)

    async def test_registration_requires_privacy_acceptance(self, db_session):
        """Test that registration fails without Privacy Policy acceptance"""
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=False,  # Not accepting privacy
        )

        with pytest.raises(Exception) as exc_info:
            await register_user(db_session, user_data)

        assert "Privacy Policy" in str(exc_info.value)

    async def test_registration_creates_consent_records(self, db_session):
        """Test that successful registration creates consent audit records"""
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )

        user_response = await register_user(db_session, user_data)

        # Verify user has consent timestamps
        assert user_response.accepted_terms is not None
        assert user_response.accepted_privacy is not None

        # Verify consent audit records were created
        query = select(ConsentAudit).where(ConsentAudit.user_id == user_response.id)
        result = await db_session.execute(query)
        consents = result.scalars().all()

        assert len(consents) == 2  # Terms and Privacy
        consent_types = {c.consent_type for c in consents}
        assert ConsentType.TERMS_OF_SERVICE in consent_types
        assert ConsentType.PRIVACY_POLICY in consent_types

        # All consents should be accepted
        assert all(c.accepted for c in consents)

    async def test_consent_timestamps_are_consistent(self, db_session):
        """Test that consent timestamps in User and ConsentAudit are consistent"""
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )

        user_response = await register_user(db_session, user_data)

        # Fetch consent audit records
        query = select(ConsentAudit).where(ConsentAudit.user_id == user_response.id)
        result = await db_session.execute(query)
        consents = result.scalars().all()

        # Timestamps should match between User and ConsentAudit
        for consent in consents:
            if consent.consent_type == ConsentType.TERMS_OF_SERVICE:
                assert consent.timestamp == user_response.accepted_terms
            elif consent.consent_type == ConsentType.PRIVACY_POLICY:
                assert consent.timestamp == user_response.accepted_privacy


@pytest.mark.asyncio
class TestDataExport:
    """
    Test user data export for GDPR compliance.

    Verifies that:
    - Users can export their personal data
    - Export includes all required fields
    - Export fails for non-existent users
    """

    async def test_export_user_data_success(self, db_session):
        """Test successful data export"""
        # Create test user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            first_name="Test",
            last_name="User",
            bio="Test bio",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Export data
        export = await export_user_data(db_session, user_response.id)

        # Verify export contains all data
        assert export.user_id == user_response.id
        assert export.email == "test@example.com"
        assert export.username == "testuser"
        assert export.first_name == "Test"
        assert export.last_name == "User"
        assert export.bio == "Test bio"
        assert export.status == "active"
        assert export.role == "consumer"
        assert export.accepted_terms is not None
        assert export.accepted_privacy is not None
        assert export.export_date is not None

    async def test_export_nonexistent_user_fails(self, db_session):
        """Test that exporting data for non-existent user fails"""
        fake_user_id = uuid4()

        with pytest.raises(GDPRError) as exc_info:
            await export_user_data(db_session, fake_user_id)

        assert "User not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestAccountDeletion:
    """
    Test account deletion with grace period.

    Verifies that:
    - Users can request account deletion
    - 30-day grace period is set
    - Account is deactivated immediately
    - User can cancel deletion during grace period
    - Cannot request deletion twice
    """

    async def test_request_account_deletion_success(self, db_session):
        """Test successful account deletion request"""
        # Create test user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Request deletion
        before_request = datetime.now(timezone.utc)
        deletion_response = await request_account_deletion(
            db_session, user_response.id, "Not using the service anymore"
        )
        after_request = datetime.now(timezone.utc)

        # Verify response
        assert deletion_response.grace_period_days == 30
        assert "30 days" in deletion_response.message
        assert deletion_response.deletion_scheduled_at > before_request
        assert deletion_response.deletion_scheduled_at < after_request + timedelta(days=31)

        # Verify user status changed
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.status == UserStatus.INACTIVE
        assert user.deletion_requested_at is not None
        assert user.deletion_scheduled_at is not None

        # Verify grace period is approximately 30 days
        grace_period = user.deletion_scheduled_at - user.deletion_requested_at
        assert 29 <= grace_period.days <= 31

    async def test_cannot_request_deletion_twice(self, db_session):
        """Test that requesting deletion twice fails"""
        # Create and delete user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)
        await request_account_deletion(db_session, user_response.id)

        # Try to request deletion again
        with pytest.raises(AccountAlreadyScheduledForDeletionError):
            await request_account_deletion(db_session, user_response.id)

    async def test_cancel_account_deletion_success(self, db_session):
        """Test successful cancellation of account deletion"""
        # Create user and request deletion
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)
        await request_account_deletion(db_session, user_response.id)

        # Cancel deletion
        await cancel_account_deletion(db_session, user_response.id)

        # Verify user status restored
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.status == UserStatus.ACTIVE
        assert user.deletion_requested_at is None
        assert user.deletion_scheduled_at is None

    async def test_cancel_deletion_without_request_fails(self, db_session):
        """Test that cancelling deletion without request fails"""
        # Create user without deletion request
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Try to cancel non-existent deletion
        with pytest.raises(GDPRError) as exc_info:
            await cancel_account_deletion(db_session, user_response.id)

        assert "No deletion request pending" in str(exc_info.value)

    async def test_execute_account_deletion_after_grace_period(self, db_session):
        """Test that account can be permanently deleted after grace period"""
        # Create user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Manually set deletion dates in the past
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        past_date = datetime.now(timezone.utc) - timedelta(days=31)
        user.deletion_requested_at = past_date
        user.deletion_scheduled_at = past_date
        await db_session.commit()

        # Execute deletion
        await execute_account_deletion(db_session, user_response.id)

        # Verify user is deleted
        query = select(User).where(User.id == user_response.id)
        result = await db_session.execute(query)
        deleted_user = result.scalar_one_or_none()

        assert deleted_user is None

        # Verify consent audit records are also deleted
        query = select(ConsentAudit).where(ConsentAudit.user_id == user_response.id)
        result = await db_session.execute(query)
        consents = result.scalars().all()

        assert len(consents) == 0

    async def test_execute_deletion_before_grace_period_fails(self, db_session):
        """Test that deletion fails if grace period hasn't expired"""
        # Create user and request deletion
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)
        await request_account_deletion(db_session, user_response.id)

        # Try to execute deletion immediately (grace period not expired)
        with pytest.raises(GDPRError) as exc_info:
            await execute_account_deletion(db_session, user_response.id)

        assert "Grace period has not expired" in str(exc_info.value)


@pytest.mark.asyncio
class TestConsentHistory:
    """
    Test consent history retrieval.

    Verifies that:
    - Users can retrieve their consent history
    - History includes all consent records
    - Records are ordered by timestamp
    """

    async def test_get_user_consents_success(self, db_session):
        """Test retrieving user consent history"""
        # Create test user
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecureP@ss1",
            accept_terms=True,
            accept_privacy=True,
        )
        user_response = await register_user(db_session, user_data)

        # Get consents
        consents = await get_user_consents(db_session, user_response.id)

        # Verify consents
        assert len(consents) == 2
        consent_types = {c.consent_type for c in consents}
        assert "terms_of_service" in consent_types
        assert "privacy_policy" in consent_types

        # All should be accepted
        assert all(c.accepted for c in consents)

        # Should have timestamps
        assert all(c.timestamp is not None for c in consents)

    async def test_get_consents_for_nonexistent_user_fails(self, db_session):
        """Test that getting consents for non-existent user fails"""
        fake_user_id = uuid4()

        with pytest.raises(GDPRError) as exc_info:
            await get_user_consents(db_session, fake_user_id)

        assert "User not found" in str(exc_info.value)
