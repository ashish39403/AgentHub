from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ToolActionStatus


class ToolActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    routine_run_id: UUID | None
    tool_name: str
    input: dict
    output: dict | None
    status: ToolActionStatus
    error: str | None
    created_at: datetime


class ToolActionLogListResponse(BaseModel):
    tool_logs: list[ToolActionLogResponse]
