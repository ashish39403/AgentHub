from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    name: str
    description: str
    category: str
    safety_level: str
    requires_confirmation: bool
    parameters: dict


class ToolListResponse(BaseModel):
    tools: list[ToolResponse]


class AgentToolsUpdate(BaseModel):
    enabled_tools: list[str] = Field(max_length=10)


class AgentToolsResponse(BaseModel):
    agent_id: str
    enabled_tools: list[str]
    tools: list[ToolResponse]
