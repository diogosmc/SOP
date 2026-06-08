"""APScheduler setup and lifecycle."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import Settings, get_settings
from app.scheduler.jobs import (
    process_due_reminders,
    process_pending_embeddings_stub,
    send_checkin,
    send_daily_summary_job,
    send_weekly_summary_job,
)

logger = logging.getLogger(__name__)

_WEEKDAY_MAP = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
}

scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def _parse_hh_mm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def should_start_scheduler(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return bool(cfg.scheduler_enabled)


def configure_scheduler(settings: Settings | None = None) -> int:
    """Register cron/interval jobs. Returns number of registered jobs."""
    cfg = settings or get_settings()
    if not cfg.scheduler_enabled:
        logger.info("scheduler_disabled")
        return 0

    if scheduler.get_jobs():
        return len(scheduler.get_jobs())

    morning_h, morning_m = _parse_hh_mm(cfg.checkin_morning_time)
    noon_h, noon_m = _parse_hh_mm(cfg.checkin_noon_time)
    evening_h, evening_m = _parse_hh_mm(cfg.checkin_evening_time)
    night_h, night_m = _parse_hh_mm(cfg.checkin_night_time)
    daily_h, daily_m = _parse_hh_mm(cfg.daily_summary_time)
    weekly_h, weekly_m = _parse_hh_mm(cfg.weekly_summary_time)
    weekly_day = _WEEKDAY_MAP.get(cfg.weekly_summary_day.lower(), "sun")

    scheduler.add_job(
        process_due_reminders,
        IntervalTrigger(minutes=1),
        id="process_due_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        send_checkin,
        CronTrigger(hour=morning_h, minute=morning_m),
        args=["morning"],
        id="checkin_morning",
        replace_existing=True,
    )
    scheduler.add_job(
        send_checkin,
        CronTrigger(hour=noon_h, minute=noon_m),
        args=["noon"],
        id="checkin_noon",
        replace_existing=True,
    )
    scheduler.add_job(
        send_checkin,
        CronTrigger(hour=evening_h, minute=evening_m),
        args=["evening"],
        id="checkin_evening",
        replace_existing=True,
    )
    scheduler.add_job(
        send_checkin,
        CronTrigger(hour=night_h, minute=night_m),
        args=["night"],
        id="checkin_night",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_summary_job,
        CronTrigger(hour=daily_h, minute=daily_m),
        id="daily_summary",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_summary_job,
        CronTrigger(day_of_week=weekly_day, hour=weekly_h, minute=weekly_m),
        id="weekly_summary",
        replace_existing=True,
    )
    scheduler.add_job(
        process_pending_embeddings_stub,
        CronTrigger(minute="*/15"),
        id="embeddings_stub",
        replace_existing=True,
    )

    count = len(scheduler.get_jobs())
    logger.info("scheduler_jobs_registered job_count=%s", count)
    return count


async def start_scheduler() -> bool:
    """Start APScheduler during application lifespan."""
    try:
        configure_scheduler()
        if not should_start_scheduler():
            return False
        if scheduler.running:
            return True
        scheduler.start()
        logger.info("scheduler_started")
        return True
    except Exception:
        logger.exception("scheduler_start_failed")
        return False


async def stop_scheduler() -> None:
    """Shut down APScheduler during application lifespan."""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("scheduler_stopped")
    except Exception:
        logger.exception("scheduler_stop_failed")


def reset_scheduler() -> None:
    """Remove all jobs and shut down — for tests only."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
    scheduler.remove_all_jobs()
