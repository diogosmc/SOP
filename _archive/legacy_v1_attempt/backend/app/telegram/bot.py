"""Telegram bot lifecycle (python-telegram-bot v21 async)."""

from __future__ import annotations

from typing import Optional

from telegram import Bot
from telegram.ext import Application, MessageHandler, filters

from app.core.config import get_settings
from app.core.logging import get_logger
from app.telegram.handlers import handle_text_message

logger = get_logger(__name__)

_bot_instance: Optional["TelegramBot"] = None


class TelegramBot:
    """Start/stop the COPILOTO Telegram bot."""

    def __init__(self) -> None:
        self.application: Application | None = None
        self._running = False

    def _build_application(self, token: str) -> Application:
        app = Application.builder().token(token).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        return app

    async def start(self) -> None:
        settings = get_settings()
        if not settings.telegram_enabled:
            logger.info("telegram_disabled")
            return
        if not settings.telegram_bot_token:
            logger.warning("telegram_missing_token")
            return
        if self._running:
            return

        self.application = self._build_application(settings.telegram_bot_token)
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        self._running = True
        logger.info("telegram_bot_started")

    async def stop(self) -> None:
        if not self.application or not self._running:
            return

        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        self.application = None
        self._running = False
        logger.info("telegram_bot_stopped")


def get_telegram_bot() -> TelegramBot:
    """Return the process-wide Telegram bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
    return _bot_instance


async def start_telegram_bot() -> None:
    await get_telegram_bot().start()


async def stop_telegram_bot() -> None:
    await get_telegram_bot().stop()


async def send_telegram_message(text: str) -> bool:
    """Send a proactive message to the configured allowed user."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_allowed_user_id:
        return False

    try:
        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=int(settings.telegram_allowed_user_id),
            text=text[:4000],
        )
        return True
    except Exception as exc:
        logger.error("telegram_send_failed", error=str(exc))
        return False
