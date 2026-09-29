from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


def parse_schedule(schedule: str, timezone: str):
    schedule = schedule.strip()
    tz = ZoneInfo(timezone)

    if schedule.startswith("daily@"):
        hour_minute = schedule.removeprefix("daily@")
        hour_text, minute_text = hour_minute.split(":", maxsplit=1)
        return CronTrigger(hour=int(hour_text), minute=int(minute_text), timezone=tz)

    if schedule.startswith("interval:minutes:"):
        minutes = int(schedule.removeprefix("interval:minutes:"))
        return IntervalTrigger(minutes=minutes, timezone=tz)

    raise ValueError("Unsupported schedule. Use daily@HH:MM or interval:minutes:N.")


async def run_scheduled_routine(routine_id: str) -> None:
    # The DB-backed scheduled runner will be wired when app lifespan scheduling is enabled.
    # Manual routine runs already use the same routine service path.
    return None
