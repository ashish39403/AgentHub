from app.integrations.gmail import fetch_recent_emails
from app.services.integration_service import get_provider_status_dict
from app.tools.context import ToolContext


async def gmail_summary(context: ToolContext, arguments: dict) -> dict:
    max_emails = int(arguments.get("max_emails", 5))
    emails = arguments.get("emails")
    if not isinstance(emails, list):
        emails = await fetch_recent_emails(user_id=context.user_id, max_emails=max_emails)

    ranked_emails = rank_emails(emails)
    action_items = extract_action_items(ranked_emails)
    connection = await get_provider_status_dict(context.session, user_id=context.user_id, provider="gmail")

    return {
        "source": "mock" if not connection["connected"] else "gmail",
        "connection": connection,
        "summary": build_email_summary(ranked_emails),
        "important_emails": ranked_emails,
        "action_items": action_items,
        "safety": {
            "read_only": True,
            "send_enabled": False,
            "delete_enabled": False,
            "message": "This tool only reads/summarizes. It cannot send or delete emails.",
        },
    }


def rank_emails(emails: list[dict]) -> list[dict]:
    ranked = []
    for email in emails:
        score = score_email(email)
        ranked.append(
            {
                "id": email.get("id"),
                "from": email.get("from"),
                "subject": email.get("subject"),
                "snippet": email.get("snippet"),
                "received_at": email.get("received_at"),
                "importance_score": score,
                "priority": "high" if score >= 60 else "medium" if score >= 30 else "low",
                "reason": reason_for_score(email, score),
            }
        )
    return sorted(ranked, key=lambda item: item["importance_score"], reverse=True)


def score_email(email: dict) -> int:
    text = f"{email.get('subject', '')} {email.get('snippet', '')}".lower()
    score = 10
    if any(term in text for term in ["interview", "internship", "deadline", "urgent", "reminder"]):
        score += 50
    if any(term in text for term in ["schedule", "due", "tomorrow", "reply"]):
        score += 25
    if "newsletter" in text:
        score -= 15
    return max(score, 0)


def reason_for_score(email: dict, score: int) -> str:
    if score >= 60:
        return "Likely important because it contains deadline, interview, scheduling, or action language."
    if score >= 30:
        return "May need review, but it is not the highest priority."
    return "Low-priority informational email."


def build_email_summary(ranked_emails: list[dict]) -> str:
    high_priority_count = sum(1 for email in ranked_emails if email["priority"] == "high")
    return f"Reviewed {len(ranked_emails)} emails. {high_priority_count} look high priority."


def extract_action_items(ranked_emails: list[dict]) -> list[str]:
    action_items = []
    for email in ranked_emails:
        if email["priority"] == "high":
            action_items.append(f"Review and respond if needed: {email['subject']}")
    return action_items or ["No urgent email action items found."]
