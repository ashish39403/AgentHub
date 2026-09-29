import json
from typing import Any, Protocol

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

from app.agents.types import AgentRuntimeMessage, LLMResponse, ToolCall, ToolDefinition


class LLMClient(Protocol):
    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        pass


class MockLLMClient:
    """Deterministic local LLM stand-in until AICredits credentials are configured."""

    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        last_message = messages[-1]

        if last_message.role == "tool":
            return LLMResponse(content=f"I used {last_message.name} and found this result: {last_message.content}")

        latest_user_message = next((message for message in reversed(messages) if message.role == "user"), None)
        if latest_user_message is None:
            return LLMResponse(content="I need a user message before I can help.")

        content = latest_user_message.content.lower()
        available_tool_names = {tool.name for tool in tools}

        if ("gmail" in content or "email" in content) and "gmail_summary" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="gmail_summary", arguments={"max_emails": 5}))

        if ("slack" in content and "send" in content) and "send_slack_message" in available_tool_names:
            return LLMResponse(
                tool_call=ToolCall(
                    name="send_slack_message",
                    arguments={
                        "channel": "#general",
                        "message": latest_user_message.content,
                    },
                )
            )

        if ("draft" in content or "message" in content or "remind" in content) and "draft_message" in available_tool_names:
            return LLMResponse(
                tool_call=ToolCall(
                    name="draft_message",
                    arguments={
                        "recipient": "there",
                        "purpose": latest_user_message.content,
                        "tone": "professional",
                    },
                )
            )

        if ("time" in content or "date" in content) and "datetime" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="datetime", arguments={}))

        return LLMResponse(content=f"{latest_user_message.content}")


class AICreditsLLMClient:
    def __init__(self, *, model: str | None = None) -> None:
        if not settings.aicredits_base_url or not settings.aicredits_api_key:
            raise RuntimeError("AICredits is selected, but AICREDITS_BASE_URL or AICREDITS_API_KEY is missing.")
        self.model = model or settings.llm_model_default
        self.client = AsyncOpenAI(
            api_key=settings.aicredits_api_key,
            base_url=settings.aicredits_base_url.rstrip("/"),
        )

    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=format_messages_for_chat_completion(messages),
                tools=[format_tool_for_chat_completion(tool) for tool in tools] or None,
                tool_choice="auto" if tools else None,
                temperature=0.2,
            )
        except OpenAIError as exc:
            raise RuntimeError(f"AICredits request failed: {exc}") from exc

        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        if tool_calls:
            function = tool_calls[0].function
            return LLMResponse(
                tool_call=ToolCall(
                    name=function.name,
                    arguments=parse_tool_arguments(function.arguments),
                )
            )
        return LLMResponse(content=message.content or "")


def format_messages_for_chat_completion(messages: list[AgentRuntimeMessage]) -> list[dict[str, str]]:
    return [format_message_for_chat_completion(message) for message in messages]


def format_message_for_chat_completion(message: AgentRuntimeMessage) -> dict[str, str]:
    if message.role == "tool":
        return {"role": "user", "content": f"Tool {message.name} returned: {message.content}"}
    return {"role": message.role, "content": message.content}


def format_tool_for_chat_completion(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def parse_tool_arguments(raw_arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_llm_client() -> LLMClient:
    if settings.llm_provider == "aicredits":
        return AICreditsLLMClient()
    return MockLLMClient()
