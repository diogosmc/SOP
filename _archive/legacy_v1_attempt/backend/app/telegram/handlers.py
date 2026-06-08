"""Telegram message handlers."""

from __future__ import annotations

import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.tools.registry import (
    handle_expense_log,
    handle_general_chat,
    handle_habit_log,
    handle_study_log,
    handle_task_creation,
    handle_workout_log,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.telegram.classifier import classify_message
from app.telegram.middleware import authorized_only

logger = get_logger(__name__)

INTENT_HANDLERS = {
    "expense_log": handle_expense_log,
    "habit_log": handle_habit_log,
    "task_creation": handle_task_creation,
    "study_log": handle_study_log,
    "workout_log": handle_workout_log,
    "general_chat": handle_general_chat,
}


@authorized_only
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Classify text, execute the matching tool, and reply briefly."""
    message = update.message
    if message is None or not message.text:
        return

    text = message.text.strip()
    if not text:
        return

    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    try:
        classification = await classify_message(text)
        handler = INTENT_HANDLERS.get(classification.intent, handle_general_chat)

        async with AsyncSessionLocal() as db:
            reply = await handler(db, user_id, classification)
            await db.commit()

        await message.reply_text(reply[:4000])
    except Exception as exc:
        logger.exception("telegram_handler_failed", error=str(exc))
        await message.reply_text("Algo deu errado. Tente de novo em instantes.")
