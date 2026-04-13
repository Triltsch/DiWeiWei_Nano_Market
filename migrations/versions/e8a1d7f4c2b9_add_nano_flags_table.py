"""Add nano_flags table and audit actions for Story 6.3 flagging

Revision ID: e8a1d7f4c2b9
Revises: c7f4d2a9b6e1
Create Date: 2026-04-13 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8a1d7f4c2b9"
down_revision: Union[str, Sequence[str], None] = "c7f4d2a9b6e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUM_FLAG_REASON = "flagreason"
_ENUM_FLAG_STATUS = "flagstatus"


def upgrade() -> None:
    """Create nano_flags table and extend auditaction enum for flag lifecycle."""
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'FLAG_CREATED'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'FLAG_REVIEWED'")

    flag_reason = sa.Enum(
        "spam",
        "copyright",
        "offensive",
        "misinformation",
        "other",
        name=_ENUM_FLAG_REASON,
    )
    flag_status = sa.Enum(
        "pending",
        "reviewed",
        "resolved",
        "closed",
        name=_ENUM_FLAG_STATUS,
    )
    flag_reason.create(op.get_bind(), checkfirst=True)
    flag_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "nano_flags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nano_id", sa.UUID(), nullable=False, comment="Flagged Nano"),
        sa.Column(
            "flagging_user_id", sa.UUID(), nullable=False, comment="User who submitted this flag"
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "spam",
                "copyright",
                "offensive",
                "misinformation",
                "other",
                name=_ENUM_FLAG_REASON,
                create_type=False,
            ),
            nullable=False,
            comment="Selected report reason",
        ),
        sa.Column(
            "comment",
            sa.String(length=500),
            nullable=True,
            comment="Optional user comment (max 500 chars)",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "reviewed",
                "resolved",
                "closed",
                name=_ENUM_FLAG_STATUS,
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="Current status of the flag workflow",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When the flag was submitted",
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When a moderator/admin reviewed this flag",
        ),
        sa.Column(
            "moderator_id",
            sa.UUID(),
            nullable=True,
            comment="Moderator/admin who reviewed this flag",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nano_id", "flagging_user_id", name="uq_nano_flags_nano_user"),
        sa.ForeignKeyConstraint(["nano_id"], ["nanos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["flagging_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["moderator_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index(op.f("ix_nano_flags_nano_id"), "nano_flags", ["nano_id"], unique=False)
    op.create_index(
        op.f("ix_nano_flags_flagging_user_id"), "nano_flags", ["flagging_user_id"], unique=False
    )
    op.create_index(op.f("ix_nano_flags_status"), "nano_flags", ["status"], unique=False)
    op.create_index(op.f("ix_nano_flags_created_at"), "nano_flags", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_nano_flags_moderator_id"), "nano_flags", ["moderator_id"], unique=False
    )


def downgrade() -> None:
    """Drop nano_flags table and enum types.

    Note: auditaction enum values are intentionally retained because PostgreSQL
    cannot safely drop individual enum values without recreating dependent types.
    """
    op.drop_index(op.f("ix_nano_flags_moderator_id"), table_name="nano_flags")
    op.drop_index(op.f("ix_nano_flags_created_at"), table_name="nano_flags")
    op.drop_index(op.f("ix_nano_flags_status"), table_name="nano_flags")
    op.drop_index(op.f("ix_nano_flags_flagging_user_id"), table_name="nano_flags")
    op.drop_index(op.f("ix_nano_flags_nano_id"), table_name="nano_flags")
    op.drop_table("nano_flags")

    sa.Enum(name=_ENUM_FLAG_STATUS).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name=_ENUM_FLAG_REASON).drop(op.get_bind(), checkfirst=True)
