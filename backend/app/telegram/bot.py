"""Telegram bot lifecycle."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.core.config import get_settings
from app.telegram.commands import cmd_chat, cmd_debug, cmd_help, cmd_resumo, cmd_start, cmd_status
from app.telegram.handlers import handle_free_text
from app.telegram.security import should_start_bot

logger = logging.getLogger(__name__)

_bot_instance: Optional["TelegramBot"] = None

ApplicationBuilder = Callable[[str], Application]


class TelegramBot:
    """Start/stop the COPILOTO Telegram Instructor bot."""

    def __init__(
        self,
        application_builder: Optional[ApplicationBuilder] = None,
    ) -> None:
        self._application_builder = application_builder
        self.application: Application | None = None
        self._running = False

    def _build_application(self, token: str) -> Application:
        if self._application_builder is not None:
            app = self._application_builder(token)
        else:
            app = Application.builder().token(token).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(CommandHandler("debug", cmd_debug))
        app.add_handler(CommandHandler("resumo", cmd_resumo))
        app.add_handler(CommandHandler("chat", cmd_chat))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text))
        return app

    async def start(self) -> bool:
        """Start polling when enabled. Returns True if the bot started."""
        settings = get_settings()
        if not should_start_bot(settings):
            logger.info("telegram_bot_not_started: disabled or missing token")
            return False
        if self._running:
            return True

        try:
            self.application = self._build_application(settings.telegram_bot_token)
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            self._running = True
            logger.info("telegram_bot_started")
            return True
        except Exception:
            logger.exception("telegram_bot_start_failed")
            self.application = None
            self._running = False
            return False

    async def stop(self) -> None:
        """Stop polling and shut down the application."""
        if not self.application or not self._running:
            return

        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        except Exception:
            logger.exception("telegram_bot_stop_failed")
        finally:
            self.application = None
            self._running = False
            logger.info("telegram_bot_stopped")

    @property
    def is_running(self) -> bool:
        return self._running


def get_telegram_bot(application_builder: Optional[ApplicationBuilder] = None) -> TelegramBot:
    """Return the process-wide Telegram bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot(application_builder=application_builder)
    return _bot_instance


def reset_telegram_bot() -> None:
    """Reset singleton — for tests only."""
    global _bot_instance
    _bot_instance = None


async def start_telegram_bot() -> bool:
    return await get_telegram_bot().start()


async def stop_telegram_bot() -> None:
    await get_telegram_bot().stop()
