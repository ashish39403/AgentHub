from uuid import UUID

from datetime import UTC, datetime
import re

from app.agents.types import AgentRunState, AgentRuntimeMessage, AgentTaskState, AgentTimingDecision
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.message import MessageCreate


SCHEDULE_PHRASES = (
    "every morning",
    "every evening",
    "every night",
    "every day",
    "every week",
    "daily",
    "tomorrow",
    "tonight",
    "schedule",
    "scheduled",
)

TIME_PATTERN = re.compile(r"\b(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)\b")
REMINDER_PATTERN = re.compile(r"\bremind\s+me\b|\breminder\b")


def create_agent_run_state(
    *,
    user: User,
    conversation: Conversation,
    payload: MessageCreate,
    runtime_messages: list[AgentRuntimeMessage],
    selected_model: str,
    routine_run_id: UUID | None,
) -> AgentRunState:
    input_message = payload.content.strip()
    runtime_messages.append(AgentRuntimeMessage(role="user", content=input_message))
    return AgentRunState(
        user_id=user.id,
        agent_id=conversation.agent_id,
        conversation_id=conversation.id,
        routine_run_id=routine_run_id,
        input_message=input_message,
        selected_model=selected_model,
        enabled_tools=conversation.agent.enabled_tools or [],
        task=classify_task(input_message=input_message, routine_run_id=routine_run_id),
        timing=decide_timing(input_message=input_message, routine_run_id=routine_run_id),
        runtime_messages=runtime_messages,
    )


def classify_task(*, input_message: str, routine_run_id: UUID | None) -> AgentTaskState:
    normalized = input_message.lower()
    if routine_run_id is not None:
        return AgentTaskState(
            kind="scheduled_routine",
            title="Scheduled routine execution",
            goal=input_message,
            requires_timing_decision=True,
            metadata={"source": "routine_run"},
        )
    if asks_for_schedule(normalized):
        return AgentTaskState(
            kind="schedule_request",
            title="Schedule request",
            goal=input_message,
            requires_timing_decision=True,
            metadata={"source": "user_message"},
        )
    if asks_for_tool_work(normalized):
        return AgentTaskState(
            kind="tool_task",
            title="Tool-backed task",
            goal=input_message,
            requires_timing_decision=False,
            metadata={"source": "user_message"},
        )
    return AgentTaskState(kind="chat", title="Chat message", goal=input_message)


def decide_timing(*, input_message: str, routine_run_id: UUID | None) -> AgentTimingDecision:
    now = datetime.now(UTC)
    normalized = input_message.lower()
    if routine_run_id is not None:
        return AgentTimingDecision(
            mode="scheduled_run",
            timezone="UTC",
            should_execute_now=True,
            reason="This run was triggered by a saved routine, so the task should execute now.",
            decided_at=now,
        )
    if asks_for_schedule(normalized):
        return AgentTimingDecision(
            mode="schedule_requested",
            timezone="UTC",
            schedule_hint=extract_schedule_hint(normalized),
            should_execute_now=False,
            reason="The user is asking for future or recurring work, so the agent should explain or prepare scheduling instead of pretending it has already run.",
            decided_at=now,
        )
    return AgentTimingDecision(
        mode="run_now",
        timezone="UTC",
        should_execute_now=True,
        reason="This is an immediate chat/task request.",
        decided_at=now,
    )


def build_state_context_message(state: AgentRunState) -> AgentRuntimeMessage:
    task = state.task or AgentTaskState(goal=state.input_message)
    timing = state.timing or decide_timing(input_message=state.input_message, routine_run_id=state.routine_run_id)
    content = "\n".join(
        [
            "<run_state>",
            f"task_kind: {task.kind}",
            f"task_goal: {task.goal}",
            f"requires_timing_decision: {task.requires_timing_decision}",
            f"timing_mode: {timing.mode}",
            f"should_execute_now: {timing.should_execute_now}",
            f"schedule_hint: {timing.schedule_hint or 'none'}",
            f"timing_reason: {timing.reason}",
            "</run_state>",
        ]
    )
    return AgentRuntimeMessage(role="system", content=content)


def attach_state_context_message(state: AgentRunState) -> None:
    if any(message.role == "system" and "<run_state>" in message.content for message in state.runtime_messages):
        return
    state.runtime_messages.append(build_state_context_message(state))


def asks_for_schedule(normalized_message: str) -> bool:
    return (
        any(phrase in normalized_message for phrase in SCHEDULE_PHRASES)
        or bool(TIME_PATTERN.search(normalized_message))
        or bool(REMINDER_PATTERN.search(normalized_message))
    )


def asks_for_tool_work(normalized_message: str) -> bool:
    return any(
        term in normalized_message
        for term in (
            "search",
            "latest",
            "gmail",
            "email",
            "notion",
            "github",
            "summarize",
            "draft",
            "remember",
            "save",
        )
    )


def extract_schedule_hint(normalized_message: str) -> str | None:
    for phrase in SCHEDULE_PHRASES:
        if phrase in normalized_message:
            return phrase
    time_match = TIME_PATTERN.search(normalized_message)
    if time_match:
        return time_match.group(0)
    return None
