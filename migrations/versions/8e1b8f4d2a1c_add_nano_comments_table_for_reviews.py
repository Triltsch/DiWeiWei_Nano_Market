"""Add nano comments table for reviews

Revision ID: 8e1b8f4d2a1c
Revises: c4b8f8b58b27
Create Date: 2026-03-24 16:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8e1b8f4d2a1c"
down_revision: Union[str, Sequence[str], None] = "c4b8f8b58b27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "nano_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nano_id", sa.UUID(), nullable=False, comment="Reviewed Nano"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="User who submitted the comment"),
        sa.Column("content", sa.Text(), nullable=False, comment="Sanitized comment content (1-1000 chars)"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(content) >= 1", name="ck_nano_comments_content_non_empty"),
        sa.CheckConstraint("length(content) <= 1000", name="ck_nano_comments_content_max_length"),
        sa.ForeignKeyConstraint(["nano_id"], ["nanos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nano_id", "user_id", name="uq_nano_comments_nano_user"),
    )
    op.create_index(op.f("ix_nano_comments_created_at"), "nano_comments", ["created_at"], unique=False)
    op.create_index(op.f("ix_nano_comments_id"), "nano_comments", ["id"], unique=False)
    op.create_index(op.f("ix_nano_comments_nano_id"), "nano_comments", ["nano_id"], unique=False)
    op.create_index(op.f("ix_nano_comments_updated_at"), "nano_comments", ["updated_at"], unique=False)
    op.create_index(op.f("ix_nano_comments_user_id"), "nano_comments", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_nano_comments_user_id"), table_name="nano_comments")
    op.drop_index(op.f("ix_nano_comments_updated_at"), table_name="nano_comments")
    op.drop_index(op.f("ix_nano_comments_nano_id"), table_name="nano_comments")
    op.drop_index(op.f("ix_nano_comments_id"), table_name="nano_comments")
    op.drop_index(op.f("ix_nano_comments_created_at"), table_name="nano_comments")
    op.drop_table("nano_comments")
