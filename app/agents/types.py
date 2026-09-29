from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRuntimeMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    category: str = "internal"
    safety_level: str = "safe"
    requires_confirmation: bool = False
    parameters: dict[str, Any]


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str | None = None
    tool_call: ToolCall | None = None

    @property
    def is_tool_call(self) -> bool:
        return self.tool_call is not None


class ToolExecutionResult(BaseModel):
    name: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None
