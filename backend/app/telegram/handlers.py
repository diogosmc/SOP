"""Telegram update handlers."""

from __future__ import annotations

import logging
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.telegram.formatter import format_telegram_reply
from app.telegram.security import UNAUTHORIZED_MESSAGE, is_user_allowed
from app.telegram.tools import route_instructor_message

logger = logging.getLogger(__name__)


def _app_user_id() -> uuid.UUID:
    return uuid.UUID(get_settings().default_user_id)


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process natural-language messages through the Instructor pipeline."""
    message = update.message
    if message is None or not message.text:
        return

    telegram_user_id = update.effective_user.id if update.effective_user else None
    if not is_user_allowed(telegram_user_id):
        await message.reply_text(UNAUTHORIZED_MESSAGE)
        return

    text = message.text.strip()
    if not text:
        return

    user_id = _app_user_id()
    try:
        async with AsyncSessionLocal() as db:
            reply = await route_instructor_message(db, user_id, text)
            await db.commit()
        await message.reply_text(format_telegram_reply(reply))
    except Exception:
        logger.exception("telegram_instructor_failed")
        await message.reply_text(
            format_telegram_reply("Algo deu errado. Tente novamente em instantes.")
        )
