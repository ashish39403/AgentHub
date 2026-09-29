"""initial schema

Revision ID: 20260929_0001
Revises:
Create Date: 2026-09-29

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260929_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

message_role = postgresql.ENUM("user", "assistant", "tool", "system", name="message_role", create_type=False)
routine_run_status = postgresql.ENUM(
    "queued",
    "running",
    "succeeded",
    "failed",
    name="routine_run_status",
    create_type=False,
)
tool_action_status = postgresql.ENUM("succeeded", "failed", name="tool_action_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    message_role.create(bind, checkfirst=True)
    routine_run_status.create(bind, checkfirst=True)
    tool_action_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "agents",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_agents_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
    )
    op.create_index(op.f("ix_agents_user_id"), "agents", ["user_id"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_conversations_agent_id_agents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_agent_id"), "conversations", ["agent_id"], unique=False)
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)

    op.create_table(
        "routines",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("schedule", sa.String(length=120), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_routines_agent_id_agents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_routines_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routines")),
    )
    op.create_index(op.f("ix_routines_agent_id"), "routines", ["agent_id"], unique=False)
    op.create_index(op.f("ix_routines_user_id"), "routines", ["user_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)

    op.create_table(
        "routine_runs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("routine_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("status", routine_run_status, nullable=False),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_routine_runs_agent_id_agents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["routine_id"],
            ["routines.id"],
            name=op.f("fk_routine_runs_routine_id_routines"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_routine_runs_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routine_runs")),
    )
    op.create_index(op.f("ix_routine_runs_agent_id"), "routine_runs", ["agent_id"], unique=False)
    op.create_index(op.f("ix_routine_runs_routine_id"), "routine_runs", ["routine_id"], unique=False)
    op.create_index(op.f("ix_routine_runs_user_id"), "routine_runs", ["user_id"], unique=False)

    op.create_table(
        "tool_action_logs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("routine_run_id", sa.Uuid(), nullable=True),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", tool_action_status, nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_tool_action_logs_agent_id_agents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["routine_run_id"],
            ["routine_runs.id"],
            name=op.f("fk_tool_action_logs_routine_run_id_routine_runs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_tool_action_logs_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_action_logs")),
    )
    op.create_index(op.f("ix_tool_action_logs_agent_id"), "tool_action_logs", ["agent_id"], unique=False)
    op.create_index(op.f("ix_tool_action_logs_routine_run_id"), "tool_action_logs", ["routine_run_id"], unique=False)
    op.create_index(op.f("ix_tool_action_logs_user_id"), "tool_action_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tool_action_logs_user_id"), table_name="tool_action_logs")
    op.drop_index(op.f("ix_tool_action_logs_routine_run_id"), table_name="tool_action_logs")
    op.drop_index(op.f("ix_tool_action_logs_agent_id"), table_name="tool_action_logs")
    op.drop_table("tool_action_logs")

    op.drop_index(op.f("ix_routine_runs_user_id"), table_name="routine_runs")
    op.drop_index(op.f("ix_routine_runs_routine_id"), table_name="routine_runs")
    op.drop_index(op.f("ix_routine_runs_agent_id"), table_name="routine_runs")
    op.drop_table("routine_runs")

    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_routines_user_id"), table_name="routines")
    op.drop_index(op.f("ix_routines_agent_id"), table_name="routines")
    op.drop_table("routines")

    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_agent_id"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index(op.f("ix_agents_user_id"), table_name="agents")
    op.drop_table("agents")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    tool_action_status.drop(bind, checkfirst=True)
    routine_run_status.drop(bind, checkfirst=True)
    message_role.drop(bind, checkfirst=True)
