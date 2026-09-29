from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    instructions: str = Field(min_length=10, max_length=8000)
    objective: str = Field(min_length=10, max_length=4000)
    enabled_tools: list[str] | None = Field(default=None, max_length=10)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    instructions: str | None = Field(default=None, min_length=10, max_length=8000)
    objective: str | None = Field(default=None, min_length=10, max_length=4000)
    enabled_tools: list[str] | None = Field(default=None, max_length=10)


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    instructions: str
    objective: str
    enabled_tools: list[str]
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
