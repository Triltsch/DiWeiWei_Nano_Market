"""Add nano ratings table for star rating

Revision ID: c4b8f8b58b27
Revises: 71e6668b4da7
Create Date: 2026-03-24 14:25:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4b8f8b58b27"
down_revision: Union[str, Sequence[str], None] = "71e6668b4da7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "nano_ratings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nano_id", sa.UUID(), nullable=False, comment="Rated Nano"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="User who submitted the rating"),
        sa.Column("score", sa.Integer(), nullable=False, comment="Star score between 1 and 5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score >= 1 AND score <= 5", name="ck_nano_ratings_score_range"),
        sa.ForeignKeyConstraint(["nano_id"], ["nanos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nano_id", "user_id", name="uq_nano_ratings_nano_user"),
    )
    op.create_index(op.f("ix_nano_ratings_created_at"), "nano_ratings", ["created_at"], unique=False)
    op.create_index(op.f("ix_nano_ratings_id"), "nano_ratings", ["id"], unique=False)
    op.create_index(op.f("ix_nano_ratings_nano_id"), "nano_ratings", ["nano_id"], unique=False)
    op.create_index(op.f("ix_nano_ratings_user_id"), "nano_ratings", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_nano_ratings_user_id"), table_name="nano_ratings")
    op.drop_index(op.f("ix_nano_ratings_nano_id"), table_name="nano_ratings")
    op.drop_index(op.f("ix_nano_ratings_id"), table_name="nano_ratings")
    op.drop_index(op.f("ix_nano_ratings_created_at"), table_name="nano_ratings")
    op.drop_table("nano_ratings")
