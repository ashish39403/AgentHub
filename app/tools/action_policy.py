SAFE_ACTION_TOOLS = {"draft_message"}
CONFIRMATION_REQUIRED_TOOLS = {"send_slack_message", "notion_create_page"}
BLOCKED_TOOLS = {"apply_to_internship", "send_email", "delete_email"}


def evaluate_action_policy(tool_name: str, arguments: dict) -> dict:
    if tool_name in SAFE_ACTION_TOOLS:
        return {"allowed": True, "requires_confirmation": False, "status": "allowed"}
    if tool_name in CONFIRMATION_REQUIRED_TOOLS:
        return {
            "allowed": False,
            "requires_confirmation": True,
            "status": "confirmation_required",
            "reason": f"{tool_name} performs an external action and requires explicit approval.",
        }
    if tool_name in BLOCKED_TOOLS:
        return {
            "allowed": False,
            "requires_confirmation": True,
            "status": "blocked",
            "reason": f"{tool_name} is not available in the MVP safety policy.",
        }
    return {"allowed": True, "requires_confirmation": False, "status": "allowed"}
