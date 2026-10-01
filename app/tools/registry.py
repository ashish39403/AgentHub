from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from app.agents.types import ToolDefinition, ToolExecutionResult
from app.tools.context import ToolContext
from app.tools.datetime_tool import get_current_datetime
from app.tools.gmail_tools import gmail_summary
from app.tools.integration_tools import github_issue_search, notion_create_page, send_slack_message
from app.tools.internal_tools import draft_message, summarize_text
from app.tools.memory_tools import get_memory, save_memory
from app.tools.search_tool import web_search

ToolHandler = Callable[[ToolContext, dict[str, Any]], Awaitable[dict[str, Any]]]


async def datetime_handler(_: ToolContext, __: dict[str, Any]) -> dict[str, Any]:
    return await get_current_datetime()


async def summarize_text_handler(_: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    return summarize_text(arguments)


async def draft_message_handler(_: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    return draft_message(arguments)


async def web_search_handler(_: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    return await web_search(arguments)


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {
            "datetime": datetime_handler,
            "web_search": web_search_handler,
            "summarize_text": summarize_text_handler,
            "save_memory": save_memory,
            "get_memory": get_memory,
            "draft_message": draft_message_handler,
            "send_slack_message": lambda _, arguments: send_slack_message(arguments),
            "gmail_summary": gmail_summary,
            "notion_create_page": notion_create_page,
            "github_issue_search": github_issue_search,
        }
        self._definitions: dict[str, ToolDefinition] = {
            "datetime": ToolDefinition(
                name="datetime",
                description="Use when the user asks for the current date, current time, timezone, or schedule timing. Returns current UTC datetime.",
                category="internal",
                safety_level="safe",
                parameters={"type": "object", "properties": {}, "additionalProperties": False},
            ),
            "web_search": ToolDefinition(
                name="web_search",
                description="Use when the user asks to search the web, find latest opportunities, research internships, or gather current external information. Uses Serper as the primary search provider. Tavily fallback is disabled by default and only runs when ENABLE_TAVILY_FALLBACK is true.",
                category="search",
                safety_level="read_only",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["query"],
                },
            ),
            "summarize_text": ToolDefinition(
                name="summarize_text",
                description="Use when the user provides text and asks to summarize, shorten, extract key points, or create a brief.",
                category="internal",
                safety_level="safe",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}, "max_chars": {"type": "integer"}},
                    "required": ["text"],
                },
            ),
            "save_memory": ToolDefinition(
                name="save_memory",
                description="Use when the user asks to save, remember, store, or persist a useful note/report for this agent.",
                category="memory",
                safety_level="safe",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["title", "content"],
                },
            ),
            "get_memory": ToolDefinition(
                name="get_memory",
                description="Use when the user asks what is saved, remembered, stored, or wants previous notes/reports for this agent.",
                category="memory",
                safety_level="read_only",
                parameters={"type": "object", "properties": {"limit": {"type": "integer"}}},
            ),
            "draft_message": ToolDefinition(
                name="draft_message",
                description="Use when the user asks to draft/write a message, email, LinkedIn note, reminder, or reply. This only creates a draft and never sends it.",
                category="action",
                safety_level="write_draft",
                parameters={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string"},
                        "purpose": {"type": "string"},
                        "tone": {"type": "string"},
                    },
                    "required": ["purpose"],
                },
            ),
            "send_slack_message": ToolDefinition(
                name="send_slack_message",
                description="Use when the user asks to send or prepare a Slack message. This prepares the action only; actual sending requires explicit confirmation.",
                category="action",
                safety_level="external_action",
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {"channel": {"type": "string"}, "message": {"type": "string"}},
                    "required": ["channel", "message"],
                },
            ),
            "gmail_summary": ToolDefinition(
                name="gmail_summary",
                description="Use when the user asks to summarize Gmail, rank important emails, triage inbox, or extract email action items. Read-only; cannot send or delete emails.",
                category="integration",
                safety_level="read_only",
                parameters={"type": "object", "properties": {"max_emails": {"type": "integer"}}},
            ),
            "notion_create_page": ToolDefinition(
                name="notion_create_page",
                description="Use when the user asks to create or prepare a Notion page. This prepares the action only and requires confirmation.",
                category="integration",
                safety_level="external_action",
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["title"],
                },
            ),
            "github_issue_search": ToolDefinition(
                name="github_issue_search",
                description="Use when the user asks to search GitHub issues, repository tasks, bugs, or open issues.",
                category="integration",
                safety_level="read_only",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            ),
        }

    def definitions(self, enabled_tools: list[str] | None = None) -> list[ToolDefinition]:
        if enabled_tools is None:
            return list(self._definitions.values())
        enabled_tool_names = set(enabled_tools)
        return [definition for name, definition in self._definitions.items() if name in enabled_tool_names]

    def tool_names(self) -> set[str]:
        return set(self._definitions)

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        context: ToolContext,
        enabled_tools: list[str],
    ) -> ToolExecutionResult:
        if name not in enabled_tools:
            return ToolExecutionResult(name=name, input=arguments, error=f"Tool '{name}' is not enabled for this agent.")

        handler = self._handlers.get(name)
        if handler is None:
            return ToolExecutionResult(name=name, input=arguments, error=f"Tool '{name}' is not available.")

        try:
            output = await handler(context, arguments)
            return ToolExecutionResult(name=name, input=arguments, output=output)
        except (ValidationError, ValueError) as exc:
            return ToolExecutionResult(name=name, input=arguments, error=str(exc))


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry()
