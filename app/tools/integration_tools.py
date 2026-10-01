from app.core.config import settings
from app.integrations.composio_client import get_composio_client
from app.services.integration_service import get_connected_account_for_provider, get_provider_status_dict
from app.tools.action_policy import evaluate_action_policy
from app.tools.context import ToolContext


async def notion_create_page(context: ToolContext, arguments: dict) -> dict:
    connection = await get_provider_status_dict(context.session, user_id=context.user_id, provider="notion")
    policy = evaluate_action_policy("notion_create_page", arguments)
    return {
        "status": policy["status"],
        "provider": "notion",
        "connection": connection,
        "title": arguments.get("title"),
        "content": arguments.get("content"),
        "requires_confirmation": policy["requires_confirmation"],
        "message": (
            "Notion page creation is prepared only. Add a confirmation endpoint before executing this write action."
            if connection["connected"]
            else "Connect Notion before creating pages."
        ),
    }


async def github_issue_search(context: ToolContext, arguments: dict) -> dict:
    query = str(arguments.get("query", "")).strip()
    if not query:
        raise ValueError("query is required")

    connection = await get_provider_status_dict(context.session, user_id=context.user_id, provider="github")
    connected_account = await get_connected_account_for_provider(
        context.session,
        user_id=context.user_id,
        provider="github",
    )
    if connected_account is None:
        return {
            "status": "not_connected",
            "provider": "github",
            "query": query,
            "connection": connection,
            "issues": [],
            "message": "Connect GitHub before searching authenticated issues.",
        }

    tool_result = await get_composio_client().execute_tool(
        tool_slug=settings.composio_github_search_tool_slug,
        user_id=str(context.user_id),
        connected_account_id=connected_account.external_connection_id or "",
        text=f"Search GitHub issues for: {query}",
    )
    if not tool_result.successful:
        return {
            "status": "failed",
            "provider": "github",
            "query": query,
            "connection": connection,
            "issues": [],
            "message": tool_result.error or "GitHub issue search failed through Composio.",
        }

    return {
        "status": "succeeded",
        "provider": "github",
        "query": query,
        "connection": connection,
        "issues": extract_github_items(tool_result.data),
        "raw_result": tool_result.data,
    }


async def send_slack_message(arguments: dict) -> dict:
    policy = evaluate_action_policy("send_slack_message", arguments)
    return {
        "status": policy["status"],
        "channel": arguments.get("channel"),
        "message": arguments.get("message"),
        "requires_confirmation": policy["requires_confirmation"],
        "reason": policy["reason"],
    }


def extract_github_items(data: dict | list | str | None) -> list[dict]:
    if isinstance(data, list):
        return [normalize_github_item(item) for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    candidates = data.get("items") or data.get("issues") or data.get("results")
    if isinstance(candidates, list):
        return [normalize_github_item(item) for item in candidates if isinstance(item, dict)]
    return [normalize_github_item(data)] if data else []


def normalize_github_item(item: dict) -> dict:
    return {
        "title": item.get("title") or item.get("name") or "Untitled GitHub item",
        "url": item.get("html_url") or item.get("url"),
        "state": item.get("state"),
        "repository": item.get("repository_url") or item.get("repository"),
        "updated_at": item.get("updated_at"),
    }
