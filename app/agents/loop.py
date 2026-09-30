from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.langgraph_runner import run_agent_graph
from app.agents.llm_client import LLMClient, get_llm_client
from app.agents.model_router import resolve_model_name
from app.agents.prompts import build_runtime_messages
from app.agents.state import create_agent_run_state
from app.agents.execution import save_user_message
from app.agents.types import ToolExecutionResult
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
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
    routine_run_id: UUID | None = None,
    llm_client: LLMClient | None = None,
    tool_registry: ToolRegistry | None = None,
    max_iterations: int | None = None,
) -> AgentLoopResult:
    selected_model = resolve_model_name(conversation.agent.model)
    llm_client = llm_client or get_llm_client(model=selected_model, temperature=conversation.agent.temperature)
    tool_registry = tool_registry or get_tool_registry()
    max_iterations = max_iterations or settings.agent_max_iterations
    state = create_agent_run_state(
        user=user,
        conversation=conversation,
        payload=payload,
        runtime_messages=build_runtime_messages(conversation),
        selected_model=selected_model,
        routine_run_id=routine_run_id,
    )

    user_message = await save_user_message(session, conversation=conversation, content=state.input_message)
    tool_context = ToolContext(session=session, user_id=user.id, agent_id=conversation.agent_id)
    graph_state = await run_agent_graph(
        session=session,
        user=user,
        conversation=conversation,
        run_state=state,
        llm_client=llm_client,
        tool_registry=tool_registry,
        tool_context=tool_context,
        max_iterations=max_iterations,
    )
    if graph_state["iterations"] >= max_iterations and graph_state["llm_response"].is_tool_call:
        await session.rollback()
        raise AgentLoopMaxIterationsError("Agent stopped after reaching the max iteration limit.")

    await session.commit()
    assistant_message = graph_state["assistant_message"]
    tool_messages = graph_state["tool_messages"]
    await session.refresh(user_message)
    await session.refresh(assistant_message)
    for tool_message in tool_messages:
        await session.refresh(tool_message)
    return AgentLoopResult(
        user_message=user_message,
        assistant_message=assistant_message,
        tool_messages=tool_messages,
        tool_results=state.tool_results,
    )
