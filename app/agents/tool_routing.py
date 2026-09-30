from app.agents.types import ToolCall


def select_forced_tool_call(content: str, enabled_tools: list[str]) -> ToolCall | None:
    enabled_tool_names = set(enabled_tools)
    normalized = content.lower()

    if "web_search" in enabled_tool_names and requires_fresh_search(normalized):
        return ToolCall(
            name="web_search",
            arguments={
                "query": build_search_query(content),
                "limit": 5,
            },
        )

    if "datetime" in enabled_tool_names and asks_for_datetime(normalized):
        return ToolCall(name="datetime", arguments={})

    return None


def requires_fresh_search(normalized_content: str) -> bool:
    freshness_terms = [
        "today",
        "latest",
        "current",
        "recent",
        "news",
        "web search",
        "search web",
        "search for",
        "find latest",
        "internship openings",
        "job openings",
        "opportunities",
    ]
    return any(term in normalized_content for term in freshness_terms)


def asks_for_datetime(normalized_content: str) -> bool:
    return any(term in normalized_content for term in ["current date", "current time", "date and time", "what time"])


def build_search_query(content: str) -> str:
    cleaned = " ".join(content.strip().split())
    prefixes = [
        "use web_search.",
        "you must call web_search.",
        "search for",
        "find latest",
    ]
    lowered = cleaned.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return cleaned[len(prefix) :].strip(" .:") or cleaned
    return cleaned
