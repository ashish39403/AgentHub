from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RoutineRunStatus


class RoutineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    routine_id: UUID
    agent_id: UUID
    status: RoutineRunStatus
    output: str | None
    error: str | None
    started_at: datetime
    finished_at: datetime | None


class RoutineRunListResponse(BaseModel):
    runs: list[RoutineRunResponse]
