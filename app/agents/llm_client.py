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


class AICreditsLLMClient:
    def __init__(self, *, model: str | None = None, temperature: float = 0.2) -> None:
        if not settings.aicredits_base_url or not settings.aicredits_api_key:
            raise RuntimeError("AICredits is selected, but AICREDITS_BASE_URL or AICREDITS_API_KEY is missing.")
        self.model = model or settings.llm_model_default
        self.temperature = temperature
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
                temperature=self.temperature,
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
        return {"role": "user", "content": format_tool_message_for_model(message)}
    return {"role": message.role, "content": message.content}


def format_tool_message_for_model(message: AgentRuntimeMessage) -> str:
    tool_name = message.name or "tool"
    try:
        payload = json.loads(message.content)
    except json.JSONDecodeError:
        return (
            f"Tool result from {tool_name}:\n"
            f"{message.content}\n\n"
            "Use this result to answer naturally. Do not expose raw tool text."
        )

    if not isinstance(payload, dict):
        return (
            f"Tool result from {tool_name}:\n"
            f"{message.content}\n\n"
            "Use this result to answer naturally. Do not expose raw tool text."
        )

    if tool_name == "web_search":
        return format_search_tool_message(payload)

    return (
        f"Tool result from {tool_name}.\n"
        f"Status: {payload.get('status', 'succeeded')}\n"
        f"Summary: {payload.get('summary') or payload.get('headline') or payload.get('message') or 'Tool completed.'}\n\n"
        "Use this result to answer naturally. Do not expose raw JSON, internal status keys, or debug fields."
    )


def format_search_tool_message(payload: dict[str, Any]) -> str:
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        return (
            "Search tool returned no usable sources.\n"
            "Say exactly: 'Search returned no results for this query.' Then suggest one refined search query."
        )

    lines = [
        "Search tool returned source data for the final answer.",
        f"Query: {payload.get('query', '')}",
        f"Status: {payload.get('status', 'succeeded')}",
        "Instructions: Use only these sources for cited claims. Do not reveal raw tool JSON or backend status fields.",
        "",
        "Sources:",
    ]
    for index, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            continue
        title = str(result.get("title") or "Untitled source")
        url = str(result.get("url") or "")
        snippet = str(result.get("snippet") or "").strip()
        lines.append(f"[{index}] {title}")
        if url:
            lines.append(f"URL: {url}")
        if snippet:
            lines.append(f"Snippet: {snippet}")
        lines.append("")
    return "\n".join(lines).strip()


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


def get_llm_client(*, model: str | None = None, temperature: float = 0.2) -> LLMClient:
    provider = settings.llm_provider.strip().lower()
    if provider == "aicredits":
        return AICreditsLLMClient(model=model, temperature=temperature)
    raise RuntimeError("LLM_PROVIDER must be set to 'aicredits' for runtime LLM calls.")
