"""Tests for Nano flag routes (Story 6.3 user reporting)."""

import uuid

import pytest
from sqlalchemy import select

from app.models import (
    CompetencyLevel,
    LicenseType,
    ModerationCase,
    ModerationContentType,
    Nano,
    NanoFlag,
    NanoFormat,
    NanoStatus,
    User,
    UserRole,
    UserStatus,
)
from app.modules.auth.tokens import create_access_token


async def _create_user(db_session, *, email: str, username: str, role: UserRole) -> User:
    """Create and flush a user for route tests."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        password_hash="dummy_hash",
        email_verified=True,
        status=UserStatus.ACTIVE,
        role=role,
        preferred_language="en",
        login_attempts=0,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_create_flag_success_creates_moderation_case(async_client, db_session):
    """Submitting a flag creates a nano_flag row and moderation case with reporter."""
    creator = await _create_user(
        db_session,
        email="flag-creator@example.com",
        username="flag_creator",
        role=UserRole.CREATOR,
    )
    reporter = await _create_user(
        db_session,
        email="flag-reporter@example.com",
        username="flag_reporter",
        role=UserRole.CONSUMER,
    )

    nano = Nano(
        id=uuid.uuid4(),
        creator_id=creator.id,
        title="Flaggable Nano",
        duration_minutes=15,
        competency_level=CompetencyLevel.BASIC,
        language="en",
        format=NanoFormat.TEXT,
        status=NanoStatus.PUBLISHED,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )
    db_session.add(nano)
    await db_session.commit()

    token, _ = create_access_token(reporter.id, reporter.email, role=reporter.role.value)
    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/flags",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "spam", "comment": "Looks like ad spam."},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["nano_id"] == str(nano.id)
    assert payload["flagging_user_id"] == str(reporter.id)
    assert payload["reason"] == "spam"
    assert payload["status"] == "pending"

    flag_id = uuid.UUID(payload["id"])

    flag = (
        await db_session.execute(select(NanoFlag).where(NanoFlag.id == flag_id))
    ).scalar_one_or_none()
    assert flag is not None

    case = (
        await db_session.execute(
            select(ModerationCase).where(
                ModerationCase.content_type == ModerationContentType.FLAG,
                ModerationCase.content_id == flag_id,
            )
        )
    ).scalar_one_or_none()
    assert case is not None
    assert case.reporter_id == reporter.id


@pytest.mark.asyncio
async def test_create_flag_duplicate_returns_409(async_client, db_session):
    """The same user cannot flag the same nano more than once."""
    creator = await _create_user(
        db_session,
        email="flag-dup-creator@example.com",
        username="flag_dup_creator",
        role=UserRole.CREATOR,
    )
    reporter = await _create_user(
        db_session,
        email="flag-dup-reporter@example.com",
        username="flag_dup_reporter",
        role=UserRole.CONSUMER,
    )

    nano = Nano(
        id=uuid.uuid4(),
        creator_id=creator.id,
        title="Duplicate Flag Nano",
        duration_minutes=20,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="en",
        format=NanoFormat.VIDEO,
        status=NanoStatus.PUBLISHED,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )
    db_session.add(nano)
    await db_session.commit()

    token, _ = create_access_token(reporter.id, reporter.email, role=reporter.role.value)

    first = await async_client.post(
        f"/api/v1/nanos/{nano.id}/flags",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "offensive", "comment": "First report"},
    )
    second = await async_client.post(
        f"/api/v1/nanos/{nano.id}/flags",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "spam", "comment": "Second report"},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert "already flagged" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_flag_forbidden_for_own_nano(async_client, db_session):
    """Creators cannot flag their own nanos."""
    creator = await _create_user(
        db_session,
        email="flag-owner@example.com",
        username="flag_owner",
        role=UserRole.CREATOR,
    )

    nano = Nano(
        id=uuid.uuid4(),
        creator_id=creator.id,
        title="Owned Nano",
        duration_minutes=10,
        competency_level=CompetencyLevel.BASIC,
        language="de",
        format=NanoFormat.MIXED,
        status=NanoStatus.PUBLISHED,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )
    db_session.add(nano)
    await db_session.commit()

    token, _ = create_access_token(creator.id, creator.email, role=creator.role.value)
    response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/flags",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "misinformation", "comment": "Should fail"},
    )

    assert response.status_code == 403
    assert "cannot flag your own nanos" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_my_flag_returns_404_then_resource(async_client, db_session):
    """My-flag endpoint returns 404 before creation and returns the flag afterwards."""
    creator = await _create_user(
        db_session,
        email="flag-my-creator@example.com",
        username="flag_my_creator",
        role=UserRole.CREATOR,
    )
    reporter = await _create_user(
        db_session,
        email="flag-my-reporter@example.com",
        username="flag_my_reporter",
        role=UserRole.CONSUMER,
    )

    nano = Nano(
        id=uuid.uuid4(),
        creator_id=creator.id,
        title="Lookup Flag Nano",
        duration_minutes=12,
        competency_level=CompetencyLevel.BASIC,
        language="en",
        format=NanoFormat.TEXT,
        status=NanoStatus.PUBLISHED,
        version="1.0.0",
        license=LicenseType.CC_BY,
    )
    db_session.add(nano)
    await db_session.commit()

    token, _ = create_access_token(reporter.id, reporter.email, role=reporter.role.value)

    not_found = await async_client.get(
        f"/api/v1/nanos/{nano.id}/flags/my-flag",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert not_found.status_code == 404

    create_response = await async_client.post(
        f"/api/v1/nanos/{nano.id}/flags",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "other", "comment": "Needs moderator review"},
    )
    assert create_response.status_code == 201

    found = await async_client.get(
        f"/api/v1/nanos/{nano.id}/flags/my-flag",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert found.status_code == 200
    payload = found.json()
    assert payload["nano_id"] == str(nano.id)
    assert payload["flagging_user_id"] == str(reporter.id)
    assert payload["reason"] == "other"
