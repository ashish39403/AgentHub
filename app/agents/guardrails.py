import json
from typing import Any


INTERNAL_KEYS = {
    "debug",
    "raw",
    "raw_result",
    "tool_calls",
    "tool_messages",
    "connection",
    "metadata",
    "status",
    "successful",
}

PREFERRED_TEXT_KEYS = ("answer", "response", "content", "summary", "message", "draft")


def guardrail_assistant_response(content: str) -> str:
    stripped = content.strip()
    if not stripped:
        return "I could not generate a useful response. Please try again with a little more detail."

    parsed = parse_json_like_content(stripped)
    if parsed is None:
        return stripped

    readable = format_structured_content(parsed)
    return readable or "I completed the request, but the result did not contain user-facing content."


def parse_json_like_content(content: str) -> Any | None:
    candidate = unwrap_json_fence(content)
    if not looks_like_json(candidate):
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def unwrap_json_fence(content: str) -> str:
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if len(lines) >= 3 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return content


def looks_like_json(content: str) -> bool:
    return (content.startswith("{") and content.endswith("}")) or (content.startswith("[") and content.endswith("]"))


def format_structured_content(value: Any) -> str:
    if isinstance(value, dict):
        return format_dict(value)
    if isinstance(value, list):
        return format_list(value)
    if isinstance(value, str):
        return value.strip()
    return str(value)


def format_dict(payload: dict[str, Any]) -> str:
    for key in PREFERRED_TEXT_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    lines: list[str] = []

    title = payload.get("title") or payload.get("headline")
    if isinstance(title, str) and title.strip():
        lines.append(f"**{title.strip()}**")

    results = payload.get("results") or payload.get("items") or payload.get("emails") or payload.get("issues")
    if isinstance(results, list) and results:
        lines.extend(format_result_items(results))

    key_values = [
        (key, value)
        for key, value in payload.items()
        if key not in INTERNAL_KEYS and key not in {"results", "items", "emails", "issues"}
    ]
    for key, value in key_values[:8]:
        line = format_key_value(key, value)
        if line:
            lines.append(line)

    return "\n".join(lines).strip()


def format_list(items: list[Any]) -> str:
    return "\n".join(format_result_items(items)).strip()


def format_result_items(items: list[Any]) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(items[:8], start=1):
        if isinstance(item, dict):
            title = item.get("title") or item.get("subject") or item.get("name") or item.get("summary")
            url = item.get("url") or item.get("html_url")
            snippet = item.get("snippet") or item.get("description") or item.get("reason")
            parts = [str(title).strip()] if title else [f"Item {index}"]
            if snippet:
                parts.append(str(snippet).strip())
            line = f"{index}. {' - '.join(part for part in parts if part)}"
            if url:
                line = f"{line}\n   Source: {url}"
            lines.append(line)
        else:
            lines.append(f"{index}. {str(item).strip()}")
    return lines


def format_key_value(key: str, value: Any) -> str | None:
    if value is None or value == "":
        return None
    label = key.replace("_", " ").strip().capitalize()
    if isinstance(value, (dict, list)):
        formatted = format_structured_content(value)
        return f"- {label}: {formatted}" if formatted else None
    return f"- {label}: {value}"
