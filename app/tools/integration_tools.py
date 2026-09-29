from app.tools.action_policy import evaluate_action_policy


async def notion_create_page(arguments: dict) -> dict:
    policy = evaluate_action_policy("notion_create_page", arguments)
    return {
        "status": policy["status"],
        "title": arguments.get("title"),
        "requires_confirmation": policy["requires_confirmation"],
        "message": policy.get("reason", "Notion page creation requires a connected Notion account."),
    }


async def github_issue_search(arguments: dict) -> dict:
    return {
        "status": "not_connected",
        "query": arguments.get("query"),
        "message": "GitHub issue search requires a connected GitHub account or public search integration.",
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
