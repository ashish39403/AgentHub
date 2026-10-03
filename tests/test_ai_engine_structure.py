from uuid import uuid4

import asyncio

from app.agents.langgraph_runner import call_model_node
from app.agents.model_router import resolve_model_name
from app.agents.prompts import build_system_prompt, build_tool_instruction
from app.agents.state import attach_state_context_message, create_agent_run_state
from app.agents.types import AgentRuntimeMessage, LLMResponse, ToolDefinition
from app.core.config import settings
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.message import MessageCreate


def test_model_router_resolves_aliases_and_fallbacks() -> None:
    assert resolve_model_name("fast") == settings.llm_model_fast
    assert resolve_model_name("smart") == settings.llm_model_smart
    assert resolve_model_name(settings.llm_model_reasoning) == settings.llm_model_reasoning
    assert resolve_model_name(None) == settings.llm_model_default
    assert resolve_model_name("unknown-model") == settings.llm_model_default


def test_prompt_builder_lists_tool_rules() -> None:
    instruction = build_tool_instruction(["web_search", "draft_message"])

    assert "web_search" in instruction
    assert "draft_message" in instruction
    assert "<tools>" in instruction
    assert "Never claim a listed tool is unavailable" in instruction


def test_system_prompt_contains_engine_rules() -> None:
    agent = Agent(
        user_id=uuid4(),
        name="Internship Research Agent",
        instructions="Find internships and summarize them clearly.",
        objective="Help a student discover relevant opportunities.",
        enabled_tools=["web_search", "save_memory"],
    )

    prompt = build_system_prompt(agent)

    assert "<identity>" in prompt
    assert "Custom instructions: Find internships" in prompt
    assert "Primary objective: Help a student" in prompt
    assert "web_search" in prompt
    assert "<freshness>" in prompt
    assert "<safety>" in prompt
    assert "<response_rules>" in prompt
    assert "<output_format>" in prompt


def test_agent_state_classifies_schedule_request_without_immediate_execution() -> None:
    user = User(id=uuid4(), name="Student", email="student@example.com", hashed_password="hashed")
    agent = Agent(
        id=uuid4(),
        user_id=user.id,
        name="Internship Agent",
        instructions="Find internships.",
        objective="Help with internship research.",
        enabled_tools=["web_search"],
    )
    conversation = Conversation(id=uuid4(), user_id=user.id, agent_id=agent.id, title="Schedule")
    conversation.agent = agent

    state = create_agent_run_state(
        user=user,
        conversation=conversation,
        payload=MessageCreate(content="Every morning find backend internships for me."),
        runtime_messages=[],
        selected_model="gpt-5-mini",
        routine_run_id=None,
    )

    assert state.task is not None
    assert state.task.kind == "schedule_request"
    assert state.timing is not None
    assert state.timing.mode == "schedule_requested"
    assert state.timing.should_execute_now is False

    attach_state_context_message(state)

    assert any("<run_state>" in message.content for message in state.runtime_messages)


def test_agent_state_marks_routine_runs_as_due_now() -> None:
    user = User(id=uuid4(), name="Student", email="routine@example.com", hashed_password="hashed")
    agent = Agent(
        id=uuid4(),
        user_id=user.id,
        name="Morning Agent",
        instructions="Run morning tasks.",
        objective="Daily routine.",
        enabled_tools=["web_search", "gmail_summary"],
    )
    conversation = Conversation(id=uuid4(), user_id=user.id, agent_id=agent.id, title="Routine")
    conversation.agent = agent
    routine_run_id = uuid4()

    state = create_agent_run_state(
        user=user,
        conversation=conversation,
        payload=MessageCreate(content="Find internships and summarize Gmail."),
        runtime_messages=[],
        selected_model="gpt-5-mini",
        routine_run_id=routine_run_id,
    )

    assert state.routine_run_id == routine_run_id
    assert state.task is not None
    assert state.task.kind == "scheduled_routine"
    assert state.timing is not None
    assert state.timing.mode == "scheduled_run"
    assert state.timing.should_execute_now is True


class ToolCountingLLMClient:
    def __init__(self) -> None:
        self.tool_counts: list[int] = []

    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.tool_counts.append(len(tools))
        return LLMResponse(content="I can help set up this schedule.")


class SingleToolRegistry:
    def definitions(self, enabled_tools: list[str] | None = None) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="web_search",
                description="Search the web.",
                category="search",
                safety_level="read_only",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            )
        ]


def test_schedule_requests_do_not_expose_live_tools_to_model() -> None:
    async def scenario() -> None:
        user = User(id=uuid4(), name="Student", email="tool-schedule@example.com", hashed_password="hashed")
        agent = Agent(
            id=uuid4(),
            user_id=user.id,
            name="Scheduler Agent",
            instructions="Schedule tasks safely.",
            objective="Test timing decisions.",
            enabled_tools=["web_search"],
        )
        conversation = Conversation(id=uuid4(), user_id=user.id, agent_id=agent.id, title="Schedule")
        conversation.agent = agent
        state = create_agent_run_state(
            user=user,
            conversation=conversation,
            payload=MessageCreate(content="Daily search internships at 9 AM."),
            runtime_messages=[],
            selected_model="gpt-5-mini",
            routine_run_id=None,
        )
        llm_client = ToolCountingLLMClient()

        result = await call_model_node(
            {
                "run_state": state,
                "tool_registry": SingleToolRegistry(),
                "llm_client": llm_client,
                "iterations": 0,
            }
        )

        assert result["iterations"] == 1
        assert llm_client.tool_counts == [0]

    asyncio.run(scenario())
