from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    enabled_tools: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    user: Mapped["User"] = relationship(back_populates="agents")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    routines: Mapped[list["Routine"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    routine_runs: Mapped[list["RoutineRun"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    tool_action_logs: Mapped[list["ToolActionLog"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    memories: Mapped[list["AgentMemory"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
