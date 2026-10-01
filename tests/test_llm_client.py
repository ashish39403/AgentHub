import json

from app.agents.llm_client import format_message_for_chat_completion
from app.agents.types import AgentRuntimeMessage


def test_tool_message_is_formatted_as_source_briefing_for_model() -> None:
    message = AgentRuntimeMessage(
        role="tool",
        name="web_search",
        content=json.dumps(
            {
                "status": "succeeded",
                "query": "latest ai news",
                "results": [
                    {
                        "title": "AI News Source",
                        "url": "https://example.com/ai",
                        "snippet": "A concise source snippet for the model to cite.",
                    }
                ],
            }
        ),
    )

    formatted = format_message_for_chat_completion(message)

    assert formatted["role"] == "user"
    assert "Search tool returned source data" in formatted["content"]
    assert "[1] AI News Source" in formatted["content"]
    assert "https://example.com/ai" in formatted["content"]
    assert "Tool web_search returned" not in formatted["content"]


def test_empty_search_tool_message_tells_model_not_to_guess() -> None:
    message = AgentRuntimeMessage(
        role="tool",
        name="web_search",
        content=json.dumps({"status": "no_results", "query": "latest ai news", "results": []}),
    )

    formatted = format_message_for_chat_completion(message)

    assert "Search tool returned no usable sources" in formatted["content"]
    assert "Search returned no results for this query." in formatted["content"]
