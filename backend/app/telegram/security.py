"""Telegram access control."""

from __future__ import annotations

from app.core.config import Settings, get_settings


UNAUTHORIZED_MESSAGE = "Acesso não autorizado."


def is_user_allowed(telegram_user_id: int | None, settings: Settings | None = None) -> bool:
    """Return True when the Telegram user matches the configured allowlist."""
    cfg = settings or get_settings()
    if telegram_user_id is None:
        return False
    if not cfg.telegram_allowed_user_id:
        return False
    try:
        allowed_id = int(cfg.telegram_allowed_user_id)
    except (TypeError, ValueError):
        return False
    return telegram_user_id == allowed_id


def should_start_bot(settings: Settings | None = None) -> bool:
    """Return True when Telegram bot should be started."""
    cfg = settings or get_settings()
    return bool(cfg.telegram_enabled and cfg.telegram_bot_token)
