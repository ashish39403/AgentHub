"""agent tool capabilities

Revision ID: 20260929_0003
Revises: 20260929_0002
Create Date: 2026-09-29

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260929_0003"
down_revision: str | None = "20260929_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("enabled_tools", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute("UPDATE agents SET enabled_tools = '[\"datetime\"]'::jsonb WHERE enabled_tools IS NULL")
    op.alter_column("agents", "enabled_tools", nullable=False)

    op.create_table(
        "agent_memories",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_agent_memories_agent_id_agents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_agent_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_memories")),
    )
    op.create_index(op.f("ix_agent_memories_agent_id"), "agent_memories", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_memories_user_id"), "agent_memories", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_memories_user_id"), table_name="agent_memories")
    op.drop_index(op.f("ix_agent_memories_agent_id"), table_name="agent_memories")
    op.drop_table("agent_memories")
    op.drop_column("agents", "enabled_tools")
