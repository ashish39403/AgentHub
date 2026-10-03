from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.types import AgentRunState, AgentRuntimeMessage, ToolCall, ToolExecutionResult
from app.models.conversation import Conversation
from app.models.enums import MessageRole, ToolActionStatus
from app.models.message import Message
from app.models.user import User
from app.repositories.conversations import create_message
from app.repositories.tool_action_logs import create_tool_action_log
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry
import json

from app.agents.tool_routing import select_forced_tool_call


async def save_user_message(session: AsyncSession, *, conversation: Conversation, content: str) -> Message:
    return await create_message(
        session,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )


async def save_assistant_message(session: AsyncSession, *, conversation: Conversation, content: str) -> Message:
    return await create_message(
        session,
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=content,
    )


async def run_forced_tool_if_needed(
    session: AsyncSession,
    *,
    state: AgentRunState,
    user: User,
    conversation: Conversation,
    tool_registry: ToolRegistry,
    tool_context: ToolContext,
) -> Message | None:
    if state.timing and not state.timing.should_execute_now:
        return None

    forced_tool_call = select_forced_tool_call(state.input_message, state.enabled_tools)
    if forced_tool_call is None:
        return None
    return await run_tool_call(
        session,
        state=state,
        user=user,
        conversation=conversation,
        tool_registry=tool_registry,
        tool_context=tool_context,
        tool_call=forced_tool_call,
    )


async def run_tool_call(
    session: AsyncSession,
    *,
    state: AgentRunState,
    user: User,
    conversation: Conversation,
    tool_registry: ToolRegistry,
    tool_context: ToolContext,
    tool_call: ToolCall,
) -> Message:
    tool_result = await execute_and_record_tool_call(
        session,
        user=user,
        conversation=conversation,
        tool_registry=tool_registry,
        tool_context=tool_context,
        enabled_tools=state.enabled_tools,
        tool_call=tool_call,
        routine_run_id=state.routine_run_id,
    )
    state.tool_results.append(tool_result)

    tool_content = format_tool_content(tool_result)
    tool_message = await create_message(
        session,
        conversation_id=conversation.id,
        role=MessageRole.TOOL,
        content=tool_content,
        tool_calls={"name": tool_result.name, "input": tool_result.input},
    )
    state.runtime_messages.append(AgentRuntimeMessage(role="tool", name=tool_result.name, content=tool_content))
    return tool_message


async def execute_and_record_tool_call(
    session: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    tool_registry: ToolRegistry,
    tool_context: ToolContext,
    enabled_tools: list[str],
    tool_call: ToolCall,
    routine_run_id: UUID | None,
) -> ToolExecutionResult:
    tool_result = await tool_registry.execute(
        tool_call.name,
        tool_call.arguments,
        context=tool_context,
        enabled_tools=enabled_tools,
    )
    await create_tool_action_log(
        session,
        user_id=user.id,
        agent_id=conversation.agent_id,
        tool_name=tool_result.name,
        input=tool_result.input,
        output=tool_result.output,
        status=ToolActionStatus.SUCCEEDED if tool_result.succeeded else ToolActionStatus.FAILED,
        routine_run_id=routine_run_id,
        error=tool_result.error,
    )
    return tool_result


def format_tool_content(tool_result: ToolExecutionResult) -> str:
    if tool_result.succeeded:
        return json.dumps(tool_result.output or {}, ensure_ascii=False)
    return f"Tool error from {tool_result.name}: {tool_result.error}"
