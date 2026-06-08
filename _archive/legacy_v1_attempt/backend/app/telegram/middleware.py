"""Telegram authorization middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]


def is_authorized_user(update: Update, settings: Settings | None = None) -> bool:
    """Return True when the sender matches TELEGRAM_ALLOWED_USER_ID."""
    cfg = settings or get_settings()
    allowed = cfg.telegram_allowed_user_id.strip()
    if not allowed:
        return False

    user = update.effective_user
    if user is None:
        return False

    return str(user.id) == allowed


async def reject_unauthorized(update: Update) -> None:
    """Notify unauthorized users without processing the message."""
    if update.message:
        await update.message.reply_text("Acesso não autorizado.")
    logger.warning(
        "telegram_unauthorized_access",
        user_id=getattr(update.effective_user, "id", None),
    )


def authorized_only(handler: Handler) -> Handler:
    """Wrap a handler so only TELEGRAM_ALLOWED_USER_ID can invoke it."""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        if not is_authorized_user(update):
            await reject_unauthorized(update)
            return None
        return await handler(update, context)

    return wrapper
