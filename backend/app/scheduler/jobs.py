"""Scheduled job implementations."""

from __future__ import annotations

import logging
import uuid

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.modules.reminders.service import ReminderService
from app.scheduler.notifications import send_notification
from app.scheduler.summaries import build_daily_summary, build_weekly_summary

logger = logging.getLogger(__name__)

CHECKIN_MESSAGES = {
    "morning": "Bom dia. Qual é sua prioridade principal hoje?",
    "noon": "Como está sua energia agora?",
    "evening": "Você vai treinar ou estudar hoje?",
    "night": "Qual foi sua principal vitória hoje?",
}


def _default_user_id() -> uuid.UUID:
    return uuid.UUID(get_settings().default_user_id)


async def process_due_reminders() -> None:
    """Send notifications for pending reminders that are due."""
    user_id = _default_user_id()
    try:
        async with AsyncSessionLocal() as db:
            service = ReminderService(db)
            due = await service.get_due_reminders(user_id)
            for reminder in due:
                body = reminder.title
                if reminder.description:
                    body = f"{body}\n{reminder.description}"
                await send_notification(f"Lembrete: {body}")
                await service.mark_sent(reminder.id, user_id)
            await db.commit()
            if due:
                logger.info("due_reminders_processed count=%s", len(due))
    except Exception:
        logger.exception("process_due_reminders_failed")


async def send_checkin(period: str) -> None:
    """Send a scheduled check-in message."""
    message = CHECKIN_MESSAGES.get(period)
    if not message:
        logger.warning("unknown_checkin_period", extra={"period": period})
        return
    await send_notification(message)
    logger.info("checkin_sent period=%s", period)


async def send_daily_summary_job() -> None:
    """Build and send the daily summary."""
    user_id = _default_user_id()
    try:
        async with AsyncSessionLocal() as db:
            summary = await build_daily_summary(user_id, db)
            await db.commit()
        await send_notification(f"Resumo diário:\n\n{summary}")
        logger.info("daily_summary_job_completed")
    except Exception:
        logger.exception("daily_summary_job_failed")


async def send_weekly_summary_job() -> None:
    """Build and send the weekly summary."""
    user_id = _default_user_id()
    try:
        async with AsyncSessionLocal() as db:
            summary = await build_weekly_summary(user_id, db)
            await db.commit()
        await send_notification(f"Resumo semanal:\n\n{summary}")
        logger.info("weekly_summary_job_completed")
    except Exception:
        logger.exception("weekly_summary_job_failed")


async def process_pending_embeddings_stub() -> None:
    """Stub job for future embedding queue processing."""
    logger.info("embeddings_stub_job_run")
