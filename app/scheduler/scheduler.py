from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import parse_schedule

scheduler = AsyncIOScheduler()


def add_routine_job(*, routine_id: str, schedule: str, timezone: str) -> None:
    trigger = parse_schedule(schedule, timezone)
    scheduler.add_job(
        "app.scheduler.jobs:run_scheduled_routine",
        trigger=trigger,
        id=f"routine:{routine_id}",
        kwargs={"routine_id": routine_id},
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )


def remove_routine_job(routine_id: str) -> None:
    job_id = f"routine:{routine_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
