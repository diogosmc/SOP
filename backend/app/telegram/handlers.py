"""Telegram update handlers."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import AsyncSessionLocal
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import format_telegram_reply
from app.telegram.instructor import _local_fallback, classify_telegram_message, process_telegram_message
from app.telegram.security import UNAUTHORIZED_MESSAGE, is_user_allowed

logger = logging.getLogger(__name__)

_DEFAULT_USER_MISSING_MESSAGE = (
    "Não consegui salvar sua mensagem porque o usuário padrão não está configurado. "
    "Execute a correção de usuário padrão."
)

_LAST_RESORT_REPLY = (
    "Entendi. Registrei como contexto. Quer que eu transforme isso em tarefa, lembrete ou nota?"
)


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process natural-language messages through the Jarvis Instructor pipeline."""
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

    logger.info(
        "telegram_message_received telegram_user_id=%s text=%s",
        telegram_user_id,
        text[:300],
    )

    user_id = None
    try:
        async with AsyncSessionLocal() as db:
            user = await ensure_default_user_exists(db)
            user_id = user.id
            reply = await process_telegram_message(db, user_id, text)
            await db.commit()
        logger.info("telegram_reply_sent user_id=%s", user_id)
        await message.reply_text(format_telegram_reply(reply))
    except IntegrityError:
        logger.exception(
            "telegram_instructor_error user_id=%s text=%s",
            user_id,
            text[:300],
        )
        await message.reply_text(format_telegram_reply(_DEFAULT_USER_MISSING_MESSAGE))
    except Exception:
        logger.exception(
            "telegram_instructor_error user_id=%s text=%s",
            user_id,
            text[:300],
        )
        classification = classify_telegram_message(text)
        fallback = _local_fallback(
            classification,
            text,
            memory_saved=False,
            tool_reply=None,
        )
        await message.reply_text(format_telegram_reply(fallback or _LAST_RESORT_REPLY))
