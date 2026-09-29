from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ToolActionStatus


class ToolActionLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_action_logs"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    routine_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("routine_runs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[ToolActionStatus] = mapped_column(
        Enum(ToolActionStatus, name="tool_action_status", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="tool_action_logs")
    agent: Mapped["Agent"] = relationship(back_populates="tool_action_logs")
    routine_run: Mapped["RoutineRun | None"] = relationship(back_populates="tool_action_logs")
