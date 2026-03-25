#!/usr/bin/env python
"""Seed reproducible QA demo data for role-based manual testing.

This script assumes the role-based QA users already exist:
- qa_consumer
- qa_creator
- qa_moderator
- qa_admin

It upserts a small set of Nanos and feedback so creator and moderator flows
can be exercised immediately in the local development environment.
"""

from __future__ import annotations

import asyncio
import io
import logging
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from minio import Minio
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings  # noqa: E402
from app.models import (  # noqa: E402
    CompetencyLevel,
    FeedbackModerationStatus,
    LicenseType,
    Nano,
    NanoComment,
    NanoFormat,
    NanoRating,
    NanoStatus,
    User,
    UserRole,
    UserStatus,
)
from app.modules.auth.password import hash_password  # noqa: E402
from app.modules.search.service import rebuild_search_index  # noqa: E402

LOGGER = logging.getLogger(__name__)
DEFAULT_DATABASE_URL = "postgresql+asyncpg://diwei_user:diwei_password@localhost:5432/diwei_nano_market"
SHARED_PASSWORD = "NanoTest123!"


@dataclass(frozen=True)
class QaUserSpec:
    """Definition of an expected QA user."""

    username: str
    email: str
    role: UserRole
    first_name: str
    last_name: str


@dataclass(frozen=True)
class QaNanoSpec:
    """Definition of a deterministic QA Nano."""

    slug: str
    title: str
    description: str
    status: NanoStatus
    duration_minutes: int
    competency_level: CompetencyLevel
    language: str
    nano_format: NanoFormat
    license_type: LicenseType
    version: str
    download_count: int
    file_storage_path: str | None


QA_USERS = {
    "consumer": QaUserSpec(
        username="qa_consumer",
        email="qa.consumer@example.com",
        role=UserRole.CONSUMER,
        first_name="QA",
        last_name="Consumer",
    ),
    "creator": QaUserSpec(
        username="qa_creator",
        email="qa.creator@example.com",
        role=UserRole.CREATOR,
        first_name="QA",
        last_name="Creator",
    ),
    "moderator": QaUserSpec(
        username="qa_moderator",
        email="qa.moderator@example.com",
        role=UserRole.MODERATOR,
        first_name="QA",
        last_name="Moderator",
    ),
    "admin": QaUserSpec(
        username="qa_admin",
        email="qa.admin@example.com",
        role=UserRole.ADMIN,
        first_name="QA",
        last_name="Admin",
    ),
}


QA_NANOS = [
    QaNanoSpec(
        slug="qa-published-feedback-demo",
        title="QA Demo: Published Nano With Feedback",
        description=(
            "Published demo Nano for validating public detail pages, downloads, ratings, "
            "comments, and moderation decisions."
        ),
        status=NanoStatus.PUBLISHED,
        duration_minutes=18,
        competency_level=CompetencyLevel.INTERMEDIATE,
        language="de",
        nano_format=NanoFormat.MIXED,
        license_type=LicenseType.CC_BY,
        version="1.2.0",
        download_count=14,
        file_storage_path="qa/demo/published-feedback.zip",
    ),
    QaNanoSpec(
        slug="qa-published-fresh-feedback",
        title="QA Demo: Published Nano For New Feedback",
        description=(
            "Published demo Nano without existing feedback so consumers can create a new "
            "rating and comment from scratch."
        ),
        status=NanoStatus.PUBLISHED,
        duration_minutes=12,
        competency_level=CompetencyLevel.BASIC,
        language="de",
        nano_format=NanoFormat.TEXT,
        license_type=LicenseType.CC_BY,
        version="1.0.0",
        download_count=2,
        file_storage_path="qa/demo/published-fresh-feedback.zip",
    ),
    QaNanoSpec(
        slug="qa-pending-review-demo",
        title="QA Demo: Pending Review Nano",
        description=(
            "Pending-review Nano for moderator queue checks and creator withdraw/resubmit flows."
        ),
        status=NanoStatus.PENDING_REVIEW,
        duration_minutes=11,
        competency_level=CompetencyLevel.BASIC,
        language="de",
        nano_format=NanoFormat.TEXT,
        license_type=LicenseType.CC_BY_SA,
        version="0.9.0",
        download_count=0,
        file_storage_path="qa/demo/pending-review.zip",
    ),
    QaNanoSpec(
        slug="qa-draft-edit-demo",
        title="QA Demo: Draft Nano",
        description="Draft Nano for creator edit and submit-for-review flows.",
        status=NanoStatus.DRAFT,
        duration_minutes=7,
        competency_level=CompetencyLevel.BASIC,
        language="en",
        nano_format=NanoFormat.QUIZ,
        license_type=LicenseType.PROPRIETARY,
        version="0.1.0",
        download_count=0,
        file_storage_path="qa/demo/draft.zip",
    ),
    QaNanoSpec(
        slug="qa-archived-demo",
        title="QA Demo: Archived Nano",
        description="Archived Nano for creator status-filter coverage.",
        status=NanoStatus.ARCHIVED,
        duration_minutes=9,
        competency_level=CompetencyLevel.ADVANCED,
        language="de",
        nano_format=NanoFormat.VIDEO,
        license_type=LicenseType.CC0,
        version="1.0.1",
        download_count=3,
        file_storage_path="qa/demo/archived.zip",
    ),
]


def _nano_thumbnail(slug: str) -> str:
    return f"https://picsum.photos/seed/{slug}/640/360"


async def _get_user_by_username(session: AsyncSession, username: str) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise RuntimeError(f"Required QA user '{username}' does not exist")
    return user


def _resolve_database_url() -> str:
    settings = get_settings()
    if settings.POSTGRES_USER and settings.POSTGRES_PASSWORD and settings.POSTGRES_DB:
        return (
            "postgresql+asyncpg://"
            f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}"
        )
    if settings.DATABASE_URL:
        if settings.DATABASE_URL.startswith("postgresql://"):
            return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return settings.DATABASE_URL
    return DEFAULT_DATABASE_URL


async def _ensure_qa_user(session: AsyncSession, spec: QaUserSpec) -> User:
    result = await session.execute(select(User).where(User.username == spec.username))
    user = result.scalar_one_or_none()
    timestamp = datetime.now(timezone.utc)

    if user is None:
        user = User(
            email=spec.email,
            username=spec.username,
            password_hash=hash_password(SHARED_PASSWORD),
            first_name=spec.first_name,
            last_name=spec.last_name,
            preferred_language="de",
            status=UserStatus.ACTIVE,
            role=spec.role,
            email_verified=True,
            verified_at=timestamp,
            accepted_terms=timestamp,
            accepted_privacy=timestamp,
        )
        session.add(user)
        await session.flush()
        return user

    user.email = spec.email
    user.password_hash = hash_password(SHARED_PASSWORD)
    user.first_name = spec.first_name
    user.last_name = spec.last_name
    user.preferred_language = "de"
    user.status = UserStatus.ACTIVE
    user.role = spec.role
    user.email_verified = True
    user.verified_at = timestamp
    if user.accepted_terms is None:
        user.accepted_terms = timestamp
    if user.accepted_privacy is None:
        user.accepted_privacy = timestamp
    await session.flush()
    return user


async def _get_existing_nano(session: AsyncSession, creator_id: UUID, spec: QaNanoSpec) -> Nano | None:
    result = await session.execute(
        select(Nano)
        .where(
            Nano.creator_id == creator_id,
            Nano.title == spec.title,
        )
        .order_by(desc(Nano.updated_at), desc(Nano.uploaded_at), desc(Nano.id))
    )
    nanos = list(result.scalars().all())
    if not nanos:
        return None

    primary_nano = nanos[0]
    for duplicate_nano in nanos[1:]:
        await session.delete(duplicate_nano)
    await session.flush()
    return primary_nano


async def _upsert_nano(session: AsyncSession, creator: User, spec: QaNanoSpec) -> Nano:
    now = datetime.now(timezone.utc)
    uploaded_at = now - timedelta(days=7)
    published_at = now - timedelta(days=3) if spec.status == NanoStatus.PUBLISHED else None
    archived_at = now - timedelta(days=1) if spec.status == NanoStatus.ARCHIVED else None
    nano = await _get_existing_nano(session, creator.id, spec)

    if nano is None:
        nano = Nano(
            creator_id=creator.id,
            title=spec.title,
            description=spec.description,
            duration_minutes=spec.duration_minutes,
            competency_level=spec.competency_level,
            language=spec.language,
            format=spec.nano_format,
            status=spec.status,
            version=spec.version,
            thumbnail_url=_nano_thumbnail(spec.slug),
            file_storage_path=spec.file_storage_path,
            license=spec.license_type,
            uploaded_at=uploaded_at,
            published_at=published_at,
            archived_at=archived_at,
            download_count=spec.download_count,
            average_rating=Decimal("0.00"),
            rating_count=0,
        )
        session.add(nano)
        await session.flush()
        return nano

    nano.title = spec.title
    nano.description = spec.description
    nano.duration_minutes = spec.duration_minutes
    nano.competency_level = spec.competency_level
    nano.language = spec.language
    nano.format = spec.nano_format
    nano.status = spec.status
    nano.version = spec.version
    nano.thumbnail_url = _nano_thumbnail(spec.slug)
    nano.file_storage_path = spec.file_storage_path
    nano.license = spec.license_type
    nano.download_count = spec.download_count
    nano.published_at = published_at
    nano.archived_at = archived_at
    await session.flush()
    return nano


async def _upsert_rating(
    session: AsyncSession,
    *,
    nano: Nano,
    user: User,
    score: int,
    status: FeedbackModerationStatus,
    moderator: User | None,
    reason: str | None,
) -> NanoRating:
    result = await session.execute(
        select(NanoRating).where(NanoRating.nano_id == nano.id, NanoRating.user_id == user.id)
    )
    rating = result.scalar_one_or_none()
    moderated_at = datetime.now(timezone.utc) if status != FeedbackModerationStatus.PENDING else None

    if rating is None:
        rating = NanoRating(nano_id=nano.id, user_id=user.id, score=score)
        session.add(rating)

    rating.score = score
    rating.moderation_status = status
    rating.moderated_at = moderated_at
    rating.moderated_by_user_id = moderator.id if moderator and moderated_at else None
    rating.moderation_reason = reason
    await session.flush()
    return rating


async def _upsert_comment(
    session: AsyncSession,
    *,
    nano: Nano,
    user: User,
    content: str,
    status: FeedbackModerationStatus,
    moderator: User | None,
    reason: str | None,
) -> NanoComment:
    result = await session.execute(
        select(NanoComment).where(NanoComment.nano_id == nano.id, NanoComment.user_id == user.id)
    )
    comment = result.scalar_one_or_none()
    moderated_at = datetime.now(timezone.utc) if status != FeedbackModerationStatus.PENDING else None

    if comment is None:
        comment = NanoComment(nano_id=nano.id, user_id=user.id, content=content)
        session.add(comment)

    comment.content = content
    comment.moderation_status = status
    comment.moderated_at = moderated_at
    comment.moderated_by_user_id = moderator.id if moderator and moderated_at else None
    comment.moderation_reason = reason
    await session.flush()
    return comment


async def _sync_rating_cache(session: AsyncSession, nano: Nano) -> None:
    result = await session.execute(
        select(NanoRating).where(
            NanoRating.nano_id == nano.id,
            NanoRating.moderation_status == FeedbackModerationStatus.APPROVED,
        )
    )
    approved_ratings = result.scalars().all()

    if not approved_ratings:
        nano.rating_count = 0
        nano.average_rating = Decimal("0.00")
        return

    total_score = sum(rating.score for rating in approved_ratings)
    nano.rating_count = len(approved_ratings)
    nano.average_rating = (Decimal(total_score) / Decimal(len(approved_ratings))).quantize(
        Decimal("0.01")
    )


def _build_demo_zip(spec: QaNanoSpec) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "README.txt",
            (
                f"{spec.title}\n\n"
                f"Status: {spec.status.value}\n"
                f"Language: {spec.language}\n"
                f"Purpose: QA demo content for manual testing.\n"
            ),
        )
    return buffer.getvalue()


def _build_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )


def _ensure_demo_object(client: Minio, spec: QaNanoSpec) -> None:
    if spec.file_storage_path is None:
        return

    payload = _build_demo_zip(spec)
    client.put_object(
        bucket_name=get_settings().MINIO_BUCKET_NAME,
        object_name=spec.file_storage_path,
        data=io.BytesIO(payload),
        length=len(payload),
        content_type="application/zip",
    )


async def seed_demo_data(database_url: str | None = None) -> dict[str, str]:
    """Create deterministic QA Nanos and feedback records."""
    resolved_database_url = database_url or _resolve_database_url()
    engine = create_async_engine(resolved_database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    minio_client = _build_minio_client()

    try:
        async with session_factory() as session:
            creator = await _ensure_qa_user(session, QA_USERS["creator"])
            consumer = await _ensure_qa_user(session, QA_USERS["consumer"])
            moderator = await _ensure_qa_user(session, QA_USERS["moderator"])
            await _ensure_qa_user(session, QA_USERS["admin"])

            nanos_by_slug: dict[str, Nano] = {}
            for spec in QA_NANOS:
                nanos_by_slug[spec.slug] = await _upsert_nano(session, creator, spec)
                _ensure_demo_object(minio_client, spec)

            published_nano = nanos_by_slug["qa-published-feedback-demo"]

            approved_rating = await _upsert_rating(
                session,
                nano=published_nano,
                user=consumer,
                score=5,
                status=FeedbackModerationStatus.APPROVED,
                moderator=moderator,
                reason="Freigegeben als sichtbare Demo-Bewertung.",
            )
            pending_rating = await _upsert_rating(
                session,
                nano=published_nano,
                user=creator,
                score=4,
                status=FeedbackModerationStatus.PENDING,
                moderator=None,
                reason=None,
            )

            approved_comment = await _upsert_comment(
                session,
                nano=published_nano,
                user=consumer,
                content="Sehr klare Struktur und sofort im Detail-View sichtbar.",
                status=FeedbackModerationStatus.APPROVED,
                moderator=moderator,
                reason="Freigegeben als sichtbarer Demo-Kommentar.",
            )
            pending_comment = await _upsert_comment(
                session,
                nano=published_nano,
                user=creator,
                content="Dieser Kommentar wartet absichtlich auf Moderation für QA-Zwecke.",
                status=FeedbackModerationStatus.PENDING,
                moderator=None,
                reason=None,
            )

            await _sync_rating_cache(session, published_nano)
            await session.commit()
            reindex_result = await rebuild_search_index(session)

            return {
                "database_url": resolved_database_url,
                "published_nano_id": str(published_nano.id),
                "fresh_feedback_nano_id": str(nanos_by_slug["qa-published-fresh-feedback"].id),
                "pending_review_nano_id": str(nanos_by_slug["qa-pending-review-demo"].id),
                "draft_nano_id": str(nanos_by_slug["qa-draft-edit-demo"].id),
                "archived_nano_id": str(nanos_by_slug["qa-archived-demo"].id),
                "approved_rating_id": str(approved_rating.id),
                "pending_rating_id": str(pending_rating.id),
                "approved_comment_id": str(approved_comment.id),
                "pending_comment_id": str(pending_comment.id),
                "search_index": str(reindex_result["index_name"]),
                "indexed_documents": str(reindex_result["document_count"]),
            }
    finally:
        await engine.dispose()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOGGER.info("Seeding QA demo data...")

    seed_result = asyncio.run(seed_demo_data())

    LOGGER.info("QA demo data ready:")
    for key, value in seed_result.items():
        LOGGER.info("  %s=%s", key, value)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())