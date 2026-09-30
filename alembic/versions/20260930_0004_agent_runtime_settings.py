"""agent runtime settings

Revision ID: 20260930_0004
Revises: 20260929_0003
Create Date: 2026-09-30

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260930_0004"
down_revision: str | None = "20260929_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("model", sa.String(length=160), nullable=True),
    )
    op.add_column(
        "agents",
        sa.Column("temperature", sa.Float(), nullable=True),
    )
    op.execute("UPDATE agents SET model = 'google/gemini-2.5-flash' WHERE model IS NULL")
    op.execute("UPDATE agents SET temperature = 0.2 WHERE temperature IS NULL")
    op.alter_column("agents", "model", nullable=False)
    op.alter_column("agents", "temperature", nullable=False)


def downgrade() -> None:
    op.drop_column("agents", "temperature")
    op.drop_column("agents", "model")
