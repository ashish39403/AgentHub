from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler.jobs import parse_schedule


def test_parse_daily_schedule() -> None:
    trigger = parse_schedule("daily@09:30", "Asia/Kolkata")

    assert isinstance(trigger, CronTrigger)


def test_parse_interval_schedule() -> None:
    trigger = parse_schedule("interval:minutes:15", "UTC")

    assert isinstance(trigger, IntervalTrigger)
