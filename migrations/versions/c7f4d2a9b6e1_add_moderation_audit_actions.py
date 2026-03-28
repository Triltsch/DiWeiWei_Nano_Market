"""Add moderation audit action enum values

Revision ID: c7f4d2a9b6e1
Revises: b2d4f8a1c3e5
Create Date: 2026-03-28 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7f4d2a9b6e1"
down_revision: Union[str, Sequence[str], None] = "b2d4f8a1c3e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add moderation action values to the PostgreSQL auditaction enum."""
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'MODERATION_APPROVED'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'MODERATION_REJECTED'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'MODERATION_DEFERRED'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'MODERATION_ESCALATED'")


def downgrade() -> None:
    """Downgrade schema.

    PostgreSQL enums do not support dropping individual values safely without
    recreating dependent objects, so this migration is intentionally a no-op.
    """
    return None
