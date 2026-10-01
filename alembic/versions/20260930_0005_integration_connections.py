"""integration connections

Revision ID: 20260930_0005
Revises: 20260930_0004
Create Date: 2026-09-30

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260930_0005"
down_revision: str | None = "20260930_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    integration_provider = postgresql.ENUM(
        "gmail",
        "notion",
        "github",
        name="integration_provider",
        create_type=False,
    )
    integration_status = postgresql.ENUM(
        "disconnected",
        "pending",
        "connected",
        "error",
        name="integration_connection_status",
        create_type=False,
    )
    integration_provider.create(op.get_bind(), checkfirst=True)
    integration_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "integration_connections",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", integration_provider, nullable=False),
        sa.Column("status", integration_status, nullable=False),
        sa.Column("account_email", sa.String(length=320), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("external_connection_id", sa.String(length=160), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_integration_connections_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_integration_connections")),
        sa.UniqueConstraint("user_id", "provider", name="uq_integration_connections_user_provider"),
    )
    op.create_index(op.f("ix_integration_connections_provider"), "integration_connections", ["provider"], unique=False)
    op.create_index(op.f("ix_integration_connections_user_id"), "integration_connections", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_integration_connections_user_id"), table_name="integration_connections")
    op.drop_index(op.f("ix_integration_connections_provider"), table_name="integration_connections")
    op.drop_table("integration_connections")
    sa.Enum(name="integration_connection_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="integration_provider").drop(op.get_bind(), checkfirst=True)
