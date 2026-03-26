"""Add chat_messages table for persistent chat message storage and polling API

Revision ID: a1b2c3d4e5f6
Revises: f3a9c2e7b1d5
Create Date: 2026-03-26 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f3a9c2e7b1d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the chat_messages table with its constraints and indexes."""
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "session_id",
            sa.UUID(),
            nullable=False,
            comment="Chat session this message belongs to",
        ),
        sa.Column(
            "sender_id",
            sa.UUID(),
            nullable=False,
            comment="User who sent the message",
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Message text content (1–1000 characters)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When the message was sent; used as polling cursor",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(content) >= 1",
            name="ck_chat_messages_content_non_empty",
        ),
        sa.CheckConstraint(
            "length(content) <= 1000",
            name="ck_chat_messages_content_max_length",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"], unique=False)
    op.create_index(
        op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_chat_messages_sender_id"), "chat_messages", ["sender_id"], unique=False
    )
    op.create_index(
        op.f("ix_chat_messages_created_at"), "chat_messages", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Drop the chat_messages table and all its indexes."""
    op.drop_index(op.f("ix_chat_messages_created_at"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_sender_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_id"), table_name="chat_messages")
    op.drop_table("chat_messages")
