from sqlalchemy import inspect

from app.agents.types import AgentRuntimeMessage
from app.models.agent import Agent
from app.models.conversation import Conversation


def build_runtime_messages(conversation: Conversation) -> list[AgentRuntimeMessage]:
    messages = [
        AgentRuntimeMessage(
            role="system",
            content=build_system_prompt(conversation.agent),
        )
    ]

    state = inspect(conversation)
    conversation_messages = (
        [] if "messages" in state.unloaded else conversation.messages
    )
    for message in sorted(conversation_messages, key=lambda item: item.created_at):
        messages.append(
            AgentRuntimeMessage(role=message.role.value, content=message.content)
        )

    return messages


def build_system_prompt(agent: Agent) -> str:
    return "\n\n".join(
        [
            f"Agent instructions: {agent.instructions}",
            f"Agent objective: {agent.objective}",
            build_tool_instruction(agent.enabled_tools or []),
            build_freshness_instruction(),
            build_safety_instruction(),
            build_response_instruction(),
            build_format_instruction(),
        ]
    )


def build_tool_instruction(enabled_tools: list[str]) -> str:
    if not enabled_tools:
        return "Tools: No tools are enabled for this agent."

    return (
        "Tools: "
        + ", ".join(enabled_tools)
        + ". When the user explicitly asks to use or call one of these tools, "
        "call it instead of saying you do not have access. After a tool returns, "
        "use the tool output as the source of truth and write a clear final "
        "answer for the user. Never claim a tool was unavailable if it is "
        "listed here."
    )


def build_freshness_instruction() -> str:
    return (
        "Freshness: For questions about today, latest, current events, news, "
        "live data, prices, openings, or anything that may have changed "
        "recently, use an available search or current-data tool before answering."
    )


def build_safety_instruction() -> str:
    return (
        "Safety: External actions that require confirmation must only be "
        "prepared, never actually sent."
    )


def build_response_instruction() -> str:
    return (
        "Response rules:\n"
        "1. Ground every answer in tool output when tools are used.\n"
        "2. Never fabricate facts. If unverified, omit it or mark it as "
        "'unverified'.\n"
        "3. Cite every claim with inline markers like [1], [2].\n"
        "4. One idea per line. Use bullets, not paragraphs.\n"
        "5. No emojis unless the user explicitly asks.\n"
        "6. No raw JSON, stack traces, or tool errors in the output.\n"
        "7. If a tool fails, say clearly: 'Search returned no results for "
        "this query.'\n"
        "8. Tone: factual, concise, unbiased. No hype, no filler.\n"
        "9. End with one optional follow-up question."
    )


def build_format_instruction() -> str:
    return (
        "Output format: Always return clean Markdown using these sections:\n"
        "# Title\n"
        "## Executive Summary\n"
        "- 3 to 5 short bullet points\n"
        "## Key Findings\n"
        "### Trend N: <Name>\n"
        "- Fact [citation]\n"
        "## Gaps & Limitations\n"
        "1. Numbered list\n"
        "## References\n"
        "| # | Source | URL |\n"
        "|---|--------|-----|\n"
        "| 1 | Name   | URL |\n\n"
        "Keep output scannable, clean, and free of any raw text dumps."
    )