"""Add moderation_cases table for content review workflow (Story 6.2)

This migration introduces the ``moderation_cases`` table, which tracks auditable
review decisions for all moderatable content types (Nanos, ratings, comments).

Key design choices:
- Unique constraint on (content_type, content_id) ensures exactly one active case
  per content item at any time.
- ``reporter_id`` is intentionally nullable and left empty for system-initiated cases;
  it will be populated by Story 6.3 (user-submitted flags).
- ``content_type`` uses a new ``moderationcontenttype`` PostgreSQL enum with a
  reserved ``flag`` value for forward compatibility.
- ``status`` uses a new ``moderationcasestatus`` enum with five lifecycle states.

Revision ID: b2d4f8a1c3e5
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28 08:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d4f8a1c3e5"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum type names created by this migration — must be dropped explicitly on
# downgrade because Alembic does not track enum types automatically.
_ENUM_MODERATION_CONTENT_TYPE = "moderationcontenttype"
_ENUM_MODERATION_CASE_STATUS = "moderationcasestatus"


def upgrade() -> None:
    """Create the moderation_cases table and its supporting enum types."""
    # Create enum types first (PostgreSQL requires explicit creation before use)
    moderation_content_type = sa.Enum(
        "NANO",
        "NANO_RATING",
        "NANO_COMMENT",
        "FLAG",
        name=_ENUM_MODERATION_CONTENT_TYPE,
    )
    moderation_case_status = sa.Enum(
        "PENDING",
        "APPROVED",
        "REJECTED",
        "DEFERRED",
        "ESCALATED",
        name=_ENUM_MODERATION_CASE_STATUS,
    )
    moderation_content_type.create(op.get_bind(), checkfirst=True)
    moderation_case_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "moderation_cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum(
                "NANO",
                "NANO_RATING",
                "NANO_COMMENT",
                "FLAG",
                name=_ENUM_MODERATION_CONTENT_TYPE,
                create_type=False,
            ),
            nullable=False,
            comment="Type of content being reviewed (nano, nano_rating, nano_comment, flag)",
        ),
        sa.Column(
            "content_id",
            sa.UUID(),
            nullable=False,
            comment="Primary key of the reviewed content record",
        ),
        sa.Column(
            "reporter_id",
            sa.UUID(),
            nullable=True,
            comment="User who reported the content (NULL for internally generated cases)",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "DEFERRED",
                "ESCALATED",
                name=_ENUM_MODERATION_CASE_STATUS,
                create_type=False,
            ),
            nullable=False,
            comment="Current review status of this case",
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
            comment="Moderator-provided reason for the decision (max 500 chars)",
        ),
        sa.Column(
            "decided_by_user_id",
            sa.UUID(),
            nullable=True,
            comment="Moderator/admin who made the most recent decision",
        ),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of the most recent decision",
        ),
        sa.Column(
            "deferred_until",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Re-review date for DEFERRED cases",
        ),
        sa.Column(
            "escalation_note",
            sa.Text(),
            nullable=True,
            comment="Reason provided when escalating to a senior moderator",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When this case was opened",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When this case was last modified",
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # One active case per content item
        sa.UniqueConstraint("content_type", "content_id", name="uq_moderation_cases_content"),
        # Foreign keys with null-safe cascade behaviour
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Indexes
    op.create_index(op.f("ix_moderation_cases_id"), "moderation_cases", ["id"], unique=False)
    op.create_index(
        op.f("ix_moderation_cases_content_id"), "moderation_cases", ["content_id"], unique=False
    )
    op.create_index(
        op.f("ix_moderation_cases_content_type"),
        "moderation_cases",
        ["content_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_cases_status"), "moderation_cases", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_moderation_cases_reporter_id"),
        "moderation_cases",
        ["reporter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_cases_created_at"),
        "moderation_cases",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the moderation_cases table and its enum types."""
    op.drop_index(op.f("ix_moderation_cases_created_at"), table_name="moderation_cases")
    op.drop_index(op.f("ix_moderation_cases_reporter_id"), table_name="moderation_cases")
    op.drop_index(op.f("ix_moderation_cases_status"), table_name="moderation_cases")
    op.drop_index(op.f("ix_moderation_cases_content_type"), table_name="moderation_cases")
    op.drop_index(op.f("ix_moderation_cases_content_id"), table_name="moderation_cases")
    op.drop_index(op.f("ix_moderation_cases_id"), table_name="moderation_cases")

    op.drop_table("moderation_cases")

    # Drop enum types explicitly — Alembic does not manage them automatically
    sa.Enum(name=_ENUM_MODERATION_CASE_STATUS).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name=_ENUM_MODERATION_CONTENT_TYPE).drop(op.get_bind(), checkfirst=True)
