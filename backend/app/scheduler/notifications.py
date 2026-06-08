"""Notification delivery for scheduled jobs."""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_notification(message: str) -> bool:
    """Send a notification via Telegram when enabled; otherwise log only."""
    settings = get_settings()
    text = message.strip()
    if not text:
        return False

    if not settings.telegram_enabled or not settings.telegram_bot_token:
        logger.info("notification_logged_only: %s", text[:200])
        return False

    if not settings.telegram_allowed_user_id:
        logger.warning("notification_missing_allowed_user_id")
        return False

    try:
        from telegram import Bot

        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=int(settings.telegram_allowed_user_id),
            text=text[:4000],
        )
        return True
    except Exception:
        logger.exception("notification_send_failed")
        return False
