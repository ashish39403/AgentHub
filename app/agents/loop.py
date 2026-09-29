from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import LLMClient, get_llm_client
from app.agents.types import AgentRuntimeMessage, ToolExecutionResult
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.enums import MessageRole, ToolActionStatus
from app.models.message import Message
from app.models.user import User
from app.repositories.conversations import create_message
from app.repositories.tool_action_logs import create_tool_action_log
from app.schemas.message import MessageCreate
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry, get_tool_registry


class AgentLoopError(RuntimeError):
    pass


class AgentLoopMaxIterationsError(AgentLoopError):
    pass


class AgentLoopResult:
    def __init__(
        self,
        *,
        user_message: Message,
        assistant_message: Message,
        tool_messages: list[Message],
        tool_results: list[ToolExecutionResult],
    ) -> None:
        self.user_message = user_message
        self.assistant_message = assistant_message
        self.tool_messages = tool_messages
        self.tool_results = tool_results


async def run_agent_loop(
    session: AsyncSession,
    *,
    user: User,
    conversation: Conversation,
    payload: MessageCreate,
    llm_client: LLMClient | None = None,
    tool_registry: ToolRegistry | None = None,
    max_iterations: int | None = None,
) -> AgentLoopResult:
    llm_client = llm_client or get_llm_client()
    tool_registry = tool_registry or get_tool_registry()
    max_iterations = max_iterations or settings.agent_max_iterations

    user_message = await create_message(
        session,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=payload.content.strip(),
    )

    runtime_messages = build_runtime_messages(conversation)
    runtime_messages.append(AgentRuntimeMessage(role="user", content=user_message.content))

    tool_messages: list[Message] = []
    tool_results: list[ToolExecutionResult] = []
    enabled_tools = conversation.agent.enabled_tools or []
    tool_context = ToolContext(session=session, user_id=user.id, agent_id=conversation.agent_id)

    for _ in range(max_iterations):
        llm_response = await llm_client.complete(
            messages=runtime_messages,
            tools=tool_registry.definitions(enabled_tools),
        )

        if not llm_response.is_tool_call:
            assistant_message = await create_message(
                session,
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=llm_response.content or "",
            )
            await session.commit()
            await session.refresh(user_message)
            await session.refresh(assistant_message)
            for tool_message in tool_messages:
                await session.refresh(tool_message)
            return AgentLoopResult(
                user_message=user_message,
                assistant_message=assistant_message,
                tool_messages=tool_messages,
                tool_results=tool_results,
            )

        tool_call = llm_response.tool_call
        assert tool_call is not None
        tool_result = await tool_registry.execute(
            tool_call.name,
            tool_call.arguments,
            context=tool_context,
            enabled_tools=enabled_tools,
        )
        tool_results.append(tool_result)

        await create_tool_action_log(
            session,
            user_id=user.id,
            agent_id=conversation.agent_id,
            tool_name=tool_result.name,
            input=tool_result.input,
            output=tool_result.output,
            status=ToolActionStatus.SUCCEEDED if tool_result.succeeded else ToolActionStatus.FAILED,
            error=tool_result.error,
        )

        tool_content = format_tool_content(tool_result)
        tool_message = await create_message(
            session,
            conversation_id=conversation.id,
            role=MessageRole.TOOL,
            content=tool_content,
            tool_calls={"name": tool_result.name, "input": tool_result.input},
        )
        tool_messages.append(tool_message)
        runtime_messages.append(AgentRuntimeMessage(role="tool", name=tool_result.name, content=tool_content))

    await session.rollback()
    raise AgentLoopMaxIterationsError("Agent stopped after reaching the max iteration limit.")


def build_runtime_messages(conversation: Conversation) -> list[AgentRuntimeMessage]:
    agent = conversation.agent
    messages = [
        AgentRuntimeMessage(
            role="system",
            content=f"Agent instructions: {agent.instructions}\nAgent objective: {agent.objective}",
        )
    ]

    state = inspect(conversation)
    conversation_messages = [] if "messages" in state.unloaded else conversation.messages
    for message in sorted(conversation_messages, key=lambda item: item.created_at):
        messages.append(AgentRuntimeMessage(role=message.role.value, content=message.content))

    return messages


def format_tool_content(tool_result: ToolExecutionResult) -> str:
    if tool_result.succeeded:
        return str(tool_result.output)
    return f"Tool error from {tool_result.name}: {tool_result.error}"
