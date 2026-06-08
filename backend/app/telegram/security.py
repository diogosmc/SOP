"""Telegram access control."""

from __future__ import annotations

import logging

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

UNAUTHORIZED_MESSAGE = "Acesso não autorizado."

_INVALID_USER_ID_PLACEHOLDERS = frozenset(
    {
        "",
        "SEU_ID",
        "YOUR_ID",
        "your_id",
        "seu_id",
        "CHANGE_ME",
        "change_me",
    }
)


def is_valid_telegram_user_id(value: str | None) -> bool:
    """Return True when TELEGRAM_ALLOWED_USER_ID is a numeric Telegram user ID."""
    if value is None:
        return False
    cleaned = value.strip()
    if not cleaned or cleaned.upper() in _INVALID_USER_ID_PLACEHOLDERS:
        return False
    if not cleaned.isdigit():
        return False
    return int(cleaned) > 0


def is_user_allowed(telegram_user_id: int | None, settings: Settings | None = None) -> bool:
    """Return True when the Telegram user matches the configured allowlist."""
    cfg = settings or get_settings()
    if telegram_user_id is None:
        return False
    if not is_valid_telegram_user_id(cfg.telegram_allowed_user_id):
        return False
    allowed_id = int(cfg.telegram_allowed_user_id.strip())
    return telegram_user_id == allowed_id


def should_start_bot(settings: Settings | None = None) -> bool:
    """Return True when Telegram bot should be started."""
    cfg = settings or get_settings()
    if not cfg.telegram_enabled or not cfg.telegram_bot_token:
        return False
    if not is_valid_telegram_user_id(cfg.telegram_allowed_user_id):
        logger.warning(
            "telegram_disabled_invalid_user_id: TELEGRAM_ALLOWED_USER_ID inválido. "
            "Use seu ID numérico (converse com @userinfobot)."
        )
        return False
    return True
