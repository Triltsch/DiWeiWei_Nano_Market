"""Add moderation fields for nano ratings and comments

Revision ID: d91f4c3e8a4b
Revises: 8e1b8f4d2a1c
Create Date: 2026-03-25 10:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d91f4c3e8a4b"
down_revision: Union[str, Sequence[str], None] = "8e1b8f4d2a1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


feedbackmoderationstatus = sa.Enum(
    "PENDING",
    "APPROVED",
    "HIDDEN",
    name="feedbackmoderationstatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    feedbackmoderationstatus.create(bind, checkfirst=True)

    op.add_column(
        "nano_ratings",
        sa.Column(
            "moderation_status",
            feedbackmoderationstatus,
            nullable=False,
            server_default=sa.text("'PENDING'"),
            comment="Moderation status for rating visibility",
        ),
    )
    op.add_column(
        "nano_ratings",
        sa.Column(
            "moderated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of latest moderation decision",
        ),
    )
    op.add_column(
        "nano_ratings",
        sa.Column(
            "moderated_by_user_id",
            sa.UUID(),
            nullable=True,
            comment="Moderator/admin who made the latest decision",
        ),
    )
    op.add_column(
        "nano_ratings",
        sa.Column(
            "moderation_reason",
            sa.Text(),
            nullable=True,
            comment="Optional reason for the latest moderation decision",
        ),
    )
    op.create_index(
        op.f("ix_nano_ratings_moderation_status"),
        "nano_ratings",
        ["moderation_status"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_nano_ratings_moderated_by_user_id_users",
        "nano_ratings",
        "users",
        ["moderated_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "nano_comments",
        sa.Column(
            "moderation_status",
            feedbackmoderationstatus,
            nullable=False,
            server_default=sa.text("'PENDING'"),
            comment="Moderation status for comment visibility",
        ),
    )
    op.add_column(
        "nano_comments",
        sa.Column(
            "moderated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of latest moderation decision",
        ),
    )
    op.add_column(
        "nano_comments",
        sa.Column(
            "moderated_by_user_id",
            sa.UUID(),
            nullable=True,
            comment="Moderator/admin who made the latest decision",
        ),
    )
    op.add_column(
        "nano_comments",
        sa.Column(
            "moderation_reason",
            sa.Text(),
            nullable=True,
            comment="Optional reason for the latest moderation decision",
        ),
    )
    op.create_index(
        op.f("ix_nano_comments_moderation_status"),
        "nano_comments",
        ["moderation_status"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_nano_comments_moderated_by_user_id_users",
        "nano_comments",
        "users",
        ["moderated_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("nano_ratings", "moderation_status", server_default=None)
    op.alter_column("nano_comments", "moderation_status", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_nano_comments_moderated_by_user_id_users",
        "nano_comments",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_nano_comments_moderation_status"), table_name="nano_comments")
    op.drop_column("nano_comments", "moderation_reason")
    op.drop_column("nano_comments", "moderated_by_user_id")
    op.drop_column("nano_comments", "moderated_at")
    op.drop_column("nano_comments", "moderation_status")

    op.drop_constraint(
        "fk_nano_ratings_moderated_by_user_id_users",
        "nano_ratings",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_nano_ratings_moderation_status"), table_name="nano_ratings")
    op.drop_column("nano_ratings", "moderation_reason")
    op.drop_column("nano_ratings", "moderated_by_user_id")
    op.drop_column("nano_ratings", "moderated_at")
    op.drop_column("nano_ratings", "moderation_status")

    feedbackmoderationstatus.drop(op.get_bind(), checkfirst=True)