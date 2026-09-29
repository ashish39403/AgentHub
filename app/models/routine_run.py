from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import RoutineRunStatus


class RoutineRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "routine_runs"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    routine_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("routines.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    status: Mapped[RoutineRunStatus] = mapped_column(
        Enum(RoutineRunStatus, name="routine_run_status", values_callable=lambda enum: [item.value for item in enum]),
        default=RoutineRunStatus.QUEUED,
        nullable=False,
    )
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="routine_runs")
    routine: Mapped["Routine"] = relationship(back_populates="runs")
    agent: Mapped["Agent"] = relationship(back_populates="routine_runs")
    tool_action_logs: Mapped[list["ToolActionLog"]] = relationship(back_populates="routine_run")
