from uuid import uuid4

from app.agents.model_router import resolve_model_name
from app.agents.prompts import build_system_prompt, build_tool_instruction
from app.core.config import settings
from app.models.agent import Agent


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
