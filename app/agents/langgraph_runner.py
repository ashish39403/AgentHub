from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution import (
    run_forced_tool_if_needed,
    run_tool_call,
    save_assistant_message,
)
from app.agents.llm_client import LLMClient
from app.agents.types import AgentRunState, LLMResponse
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry


class AgentGraphState(TypedDict, total=False):
    session: AsyncSession
    user: User
    conversation: Conversation
    run_state: AgentRunState
    llm_client: LLMClient
    tool_registry: ToolRegistry
    tool_context: ToolContext
    tool_messages: list[Message]
    assistant_message: Message
    llm_response: LLMResponse
    iterations: int
    max_iterations: int


async def run_agent_graph(
    *,
    session: AsyncSession,
    user: User,
    conversation: Conversation,
    run_state: AgentRunState,
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
    tool_context: ToolContext,
    max_iterations: int,
) -> AgentGraphState:
    graph = build_agent_graph()
    initial_state: AgentGraphState = {
        "session": session,
        "user": user,
        "conversation": conversation,
        "run_state": run_state,
        "llm_client": llm_client,
        "tool_registry": tool_registry,
        "tool_context": tool_context,
        "tool_messages": [],
        "iterations": 0,
        "max_iterations": max_iterations,
    }
    return await graph.ainvoke(initial_state)


def build_agent_graph() -> Any:
    builder = StateGraph(AgentGraphState)
    builder.add_node("run_forced_tool", run_forced_tool_node)
    builder.add_node("call_model", call_model_node)
    builder.add_node("execute_tool", execute_tool_node)
    builder.add_node("save_final_answer", save_final_answer_node)
    builder.set_entry_point("run_forced_tool")
    builder.add_edge("run_forced_tool", "call_model")
    builder.add_conditional_edges(
        "call_model",
        route_after_model,
        {
            "execute_tool": "execute_tool",
            "save_final_answer": "save_final_answer",
            "max_iterations": "save_final_answer",
        },
    )
    builder.add_edge("execute_tool", "call_model")
    builder.add_edge("save_final_answer", END)
    return builder.compile()


async def run_forced_tool_node(state: AgentGraphState) -> dict[str, Any]:
    tool_message = await run_forced_tool_if_needed(
        state["session"],
        state=state["run_state"],
        user=state["user"],
        conversation=state["conversation"],
        tool_registry=state["tool_registry"],
        tool_context=state["tool_context"],
    )
    if tool_message is None:
        return {}
    return {"tool_messages": [*state["tool_messages"], tool_message]}


async def call_model_node(state: AgentGraphState) -> dict[str, Any]:
    run_state = state["run_state"]
    llm_response = await state["llm_client"].complete(
        messages=run_state.runtime_messages,
        tools=state["tool_registry"].definitions(run_state.enabled_tools),
    )
    return {
        "llm_response": llm_response,
        "iterations": state["iterations"] + 1,
    }


def route_after_model(state: AgentGraphState) -> Literal["execute_tool", "save_final_answer", "max_iterations"]:
    llm_response = state["llm_response"]
    if not llm_response.is_tool_call:
        return "save_final_answer"
    if state["iterations"] >= state["max_iterations"]:
        return "max_iterations"
    return "execute_tool"


async def execute_tool_node(state: AgentGraphState) -> dict[str, Any]:
    tool_call = state["llm_response"].tool_call
    if tool_call is None:
        return {}

    tool_message = await run_tool_call(
        state["session"],
        state=state["run_state"],
        user=state["user"],
        conversation=state["conversation"],
        tool_registry=state["tool_registry"],
        tool_context=state["tool_context"],
        tool_call=tool_call,
    )
    return {"tool_messages": [*state["tool_messages"], tool_message]}


async def save_final_answer_node(state: AgentGraphState) -> dict[str, Any]:
    llm_response = state["llm_response"]
    content = llm_response.content or ""
    run_state = state["run_state"]
    run_state.final_answer = content
    assistant_message = await save_assistant_message(
        state["session"],
        conversation=state["conversation"],
        content=content,
    )
    return {"assistant_message": assistant_message}
