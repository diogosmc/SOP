"""APScheduler setup and lifespan hooks."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.logging import get_logger
from app.scheduler.jobs.checkins import send_checkin
from app.scheduler.jobs.embeddings import process_unindexed_notes
from app.scheduler.jobs.summaries import send_daily_summary, send_weekly_summary

logger = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def _parse_hh_mm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def configure_scheduler() -> None:
    """Register cron jobs from settings."""
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("scheduler_disabled")
        return

    if scheduler.get_jobs():
        return

    morning_h, morning_m = _parse_hh_mm(settings.checkin_morning)
    noon_h, noon_m = _parse_hh_mm(settings.checkin_noon)
    evening_h, evening_m = _parse_hh_mm(settings.checkin_evening)
    night_h, night_m = _parse_hh_mm(settings.checkin_night)
    daily_h, daily_m = _parse_hh_mm(settings.daily_summary_time)
    weekly_h, weekly_m = _parse_hh_mm(settings.weekly_summary_time)

    scheduler.add_job(send_checkin, CronTrigger(hour=morning_h, minute=morning_m), args=["morning"], id="checkin_morning")
    scheduler.add_job(send_checkin, CronTrigger(hour=noon_h, minute=noon_m), args=["noon"], id="checkin_noon")
    scheduler.add_job(send_checkin, CronTrigger(hour=evening_h, minute=evening_m), args=["evening"], id="checkin_evening")
    scheduler.add_job(send_checkin, CronTrigger(hour=night_h, minute=night_m), args=["night"], id="checkin_night")
    scheduler.add_job(send_daily_summary, CronTrigger(hour=daily_h, minute=daily_m), id="daily_summary")
    scheduler.add_job(
        send_weekly_summary,
        CronTrigger(day_of_week=settings.weekly_summary_day, hour=weekly_h, minute=weekly_m),
        id="weekly_summary",
    )
    scheduler.add_job(process_unindexed_notes, CronTrigger(minute="*/15"), id="embeddings_batch")

    logger.info("scheduler_jobs_registered", job_count=len(scheduler.get_jobs()))


async def start_scheduler() -> None:
    """Start APScheduler during application lifespan."""
    configure_scheduler()
    if not get_settings().scheduler_enabled:
        return
    if scheduler.running:
        return
    scheduler.start()
    logger.info("scheduler_started")


async def stop_scheduler() -> None:
    """Shut down APScheduler during application lifespan."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
