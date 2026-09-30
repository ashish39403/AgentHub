from datetime import UTC, datetime, timedelta

from app.integrations.composio_client import get_composio_client


async def get_gmail_connection_status(*, user_id) -> dict:
    configured = get_composio_client().is_configured()
    return {
        "provider": "gmail",
        "configured": configured,
        "connected": False,
        "status": "disconnected",
        "message": "Use the integration service with a database session for user-scoped Gmail connection status.",
    }


async def fetch_recent_emails(*, user_id, max_emails: int = 5) -> list[dict]:
    # Deterministic local data keeps the Gmail summary feature testable until
    # the Composio OAuth connection flow is available.
    now = datetime.now(UTC)
    return [
        {
            "id": "email_1",
            "from": "recruiter@cloudbridge.example",
            "subject": "Backend Engineering Internship Interview",
            "snippet": "We reviewed your profile and would like to schedule an interview this week.",
            "received_at": (now - timedelta(hours=2)).isoformat(),
            "labels": ["INBOX", "IMPORTANT"],
        },
        {
            "id": "email_2",
            "from": "newsletter@example.com",
            "subject": "Weekly developer newsletter",
            "snippet": "A roundup of tutorials, product launches, and community links.",
            "received_at": (now - timedelta(hours=5)).isoformat(),
            "labels": ["INBOX", "CATEGORY_UPDATES"],
        },
        {
            "id": "email_3",
            "from": "college@example.edu",
            "subject": "Project submission deadline reminder",
            "snippet": "Reminder that your project submission is due tomorrow before 5 PM.",
            "received_at": (now - timedelta(hours=8)).isoformat(),
            "labels": ["INBOX"],
        },
    ][:max_emails]
