from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoutineCreate(BaseModel):
    agent_id: UUID
    name: str = Field(min_length=2, max_length=160)
    prompt: str = Field(min_length=3, max_length=20000)
    schedule: str = Field(min_length=3, max_length=120)
    timezone: str = Field(default="UTC", min_length=2, max_length=80)
    is_active: bool = True


class RoutineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    prompt: str | None = Field(default=None, min_length=3, max_length=20000)
    schedule: str | None = Field(default=None, min_length=3, max_length=120)
    timezone: str | None = Field(default=None, min_length=2, max_length=80)
    is_active: bool | None = None


class RoutineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    agent_id: UUID
    name: str
    prompt: str
    schedule: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoutineListResponse(BaseModel):
    routines: list[RoutineResponse]
