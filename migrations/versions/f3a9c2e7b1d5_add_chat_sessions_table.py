"""Add chat_sessions table for chat session API

Revision ID: f3a9c2e7b1d5
Revises: d91f4c3e8a4b
Create Date: 2026-03-26 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a9c2e7b1d5"
down_revision: Union[str, Sequence[str], None] = "d91f4c3e8a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the chat_sessions table with its constraints and indexes."""
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "nano_id",
            sa.UUID(),
            nullable=False,
            comment="Referenced Nano for the chat context",
        ),
        sa.Column(
            "creator_id",
            sa.UUID(),
            nullable=False,
            comment="Nano creator participating in this chat",
        ),
        sa.Column(
            "participant_user_id",
            sa.UUID(),
            nullable=False,
            comment="Non-creator participant in this chat",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of last message in this session",
        ),
        sa.CheckConstraint(
            "creator_id <> participant_user_id",
            name="ck_chat_sessions_distinct_participants",
        ),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["nano_id"], ["nanos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "nano_id",
            "creator_id",
            "participant_user_id",
            name="uq_chat_sessions_nano_creator_participant",
        ),
    )
    op.create_index(op.f("ix_chat_sessions_id"), "chat_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_chat_sessions_nano_id"), "chat_sessions", ["nano_id"], unique=False
    )
    op.create_index(
        op.f("ix_chat_sessions_creator_id"), "chat_sessions", ["creator_id"], unique=False
    )
    op.create_index(
        op.f("ix_chat_sessions_participant_user_id"),
        "chat_sessions",
        ["participant_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_sessions_created_at"), "chat_sessions", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_chat_sessions_updated_at"), "chat_sessions", ["updated_at"], unique=False
    )
    op.create_index(
        op.f("ix_chat_sessions_last_message_at"),
        "chat_sessions",
        ["last_message_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the chat_sessions table and all its indexes."""
    op.drop_index(op.f("ix_chat_sessions_last_message_at"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_updated_at"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_created_at"), table_name="chat_sessions")
    op.drop_index(
        op.f("ix_chat_sessions_participant_user_id"), table_name="chat_sessions"
    )
    op.drop_index(op.f("ix_chat_sessions_creator_id"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_nano_id"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")
