from datetime import datetime
from typing import Any, Literal
from uuid import UUID

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


class AgentTaskState(BaseModel):
    kind: Literal["chat", "scheduled_routine", "schedule_request", "tool_task"] = "chat"
    title: str | None = None
    goal: str
    requires_timing_decision: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTimingDecision(BaseModel):
    mode: Literal["run_now", "schedule_requested", "scheduled_run"] = "run_now"
    timezone: str = "UTC"
    schedule_hint: str | None = None
    should_execute_now: bool = True
    reason: str
    decided_at: datetime


class AgentRunState(BaseModel):
    user_id: UUID
    agent_id: UUID
    conversation_id: UUID
    routine_run_id: UUID | None = None
    input_message: str
    selected_model: str | None = None
    enabled_tools: list[str] = Field(default_factory=list)
    task: AgentTaskState | None = None
    timing: AgentTimingDecision | None = None
    runtime_messages: list[AgentRuntimeMessage] = Field(default_factory=list)
    tool_results: list[ToolExecutionResult] = Field(default_factory=list)
    final_answer: str | None = None
    error: str | None = None
