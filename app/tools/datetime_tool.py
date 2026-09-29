from datetime import UTC, datetime


async def get_current_datetime() -> dict:
    now = datetime.now(UTC)
    return {
        "iso": now.isoformat(),
        "timezone": "UTC",
    }
