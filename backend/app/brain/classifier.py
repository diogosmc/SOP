"""Message classification wrapper for Conversation Brain."""

from __future__ import annotations

from typing import Any


def classify_message(text: str) -> dict[str, Any]:
    from app.telegram.instructor import classify_telegram_message

    return classify_telegram_message(text)
