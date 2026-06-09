"""Telegram update handlers."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from app.brain.telegram_streamer import stream_telegram_response
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import format_telegram_reply, reply_telegram
from app.telegram.instructor import _local_fallback, classify_telegram_message
from app.telegram.security import UNAUTHORIZED_MESSAGE, is_user_allowed

logger = logging.getLogger(__name__)

_DEFAULT_USER_MISSING_MESSAGE = (
    "Não consegui salvar sua mensagem porque o usuário padrão não está configurado. "
    "Execute a correção de usuário padrão."
)

_LAST_RESORT_REPLY = (
    "Entendi. Vou guardar isso como contexto para te responder melhor nas próximas."
)


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process natural-language messages through the Conversation Brain."""
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

    settings = get_settings()
    user_id = None

    try:
        from app.brain.conversation_manager import process_message

        async with AsyncSessionLocal() as db:
            user = await ensure_default_user_exists(db)
            user_id = user.id

            async def _factory():
                brain_result = await process_message(
                    db,
                    user_id,
                    text,
                    origin="telegram",
                    prefer_speed=True,
                    allow_tools=True,
                    allow_llm=True,
                )
                await db.commit()
                return brain_result

            if settings.telegram_streaming_enabled:
                result = await stream_telegram_response(message, _factory)
            else:
                result = await _factory()
                await reply_telegram(message, result.response, html=True)

            logger.info(
                "telegram_reply_sent user_id=%s intent=%s ms=%s",
                user_id,
                result.intent,
                result.response_time_ms,
            )
    except IntegrityError:
        logger.exception(
            "telegram_instructor_error user_id=%s text=%s",
            user_id,
            text[:300],
        )
        await reply_telegram(message, _DEFAULT_USER_MISSING_MESSAGE, html=False)
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
        await reply_telegram(message, fallback or _LAST_RESORT_REPLY, html=True)
