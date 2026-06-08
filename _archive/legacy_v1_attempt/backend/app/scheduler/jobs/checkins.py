"""Scheduled check-in messages."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.telegram.bot import send_telegram_message

logger = get_logger(__name__)

CHECKIN_MESSAGES = {
    "morning": "Bom dia.\n\nQual é a prioridade principal de hoje?",
    "noon": "Meio-dia.\n\nComo está indo o dia até aqui?",
    "evening": "Boa tarde.\n\nO que ainda falta fazer hoje?",
    "night": "Boa noite.\n\nComo foi seu dia?\n\nQual foi sua principal vitória?",
}


async def send_checkin(period: str) -> None:
    """Send a check-in message for morning, noon, evening, or night."""
    settings = get_settings()
    if not settings.telegram_enabled:
        return

    message = CHECKIN_MESSAGES.get(period)
    if not message:
        logger.warning("checkin_unknown_period", period=period)
        return

    sent = await send_telegram_message(message)
    if sent:
        logger.info("checkin_sent", period=period)
