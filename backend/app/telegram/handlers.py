"""Telegram update handlers."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import AsyncSessionLocal
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import format_telegram_reply
from app.telegram.security import UNAUTHORIZED_MESSAGE, is_user_allowed
from app.telegram.tools import route_instructor_message

logger = logging.getLogger(__name__)

_DEFAULT_USER_MISSING_MESSAGE = (
    "Não consegui salvar sua mensagem porque o usuário padrão não está configurado. "
    "Execute a correção de usuário padrão."
)


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

    try:
        async with AsyncSessionLocal() as db:
            user = await ensure_default_user_exists(db)
            reply = await route_instructor_message(db, user.id, text)
            await db.commit()
        await message.reply_text(format_telegram_reply(reply))
    except IntegrityError:
        logger.exception("telegram_instructor_integrity_error")
        await message.reply_text(format_telegram_reply(_DEFAULT_USER_MISSING_MESSAGE))
    except Exception:
        logger.exception("telegram_instructor_failed")
        await message.reply_text(
            format_telegram_reply("Algo deu errado. Tente novamente em instantes.")
        )
