"""Daily journal updates from classified chat messages."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.memory.repository import MemoryRepository


def _today() -> date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


def _append_summary(current: str | None, addition: str) -> str:
    addition = addition.strip()
    if not addition:
        return current or ""
    if not current:
        return addition
    if addition in current:
        return current
    return f"{current}\n{addition}"


def _mood_from_text(text: str) -> int | None:
    lowered = text.lower()
    if any(word in lowered for word in ("desanimado", "triste", "mal", "péssimo", "pessimo")):
        return 3
    if any(word in lowered for word in ("ansioso", "estressado", "preocupado")):
        return 4
    if any(word in lowered for word in ("feliz", "motivado", "bem", "grato")):
        return 8
    return 5


async def update_daily_journal_from_message(
    user_id: uuid.UUID,
    message: str,
    classification: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Incrementally update today's journal entry from a classified message."""
    if not classification.get("should_save_memory") and classification.get("intent") not in {
        "study_log",
        "study_plan",
        "workout_log",
        "expense_log",
        "emotional_checkin",
        "goal_update",
        "habit_log",
        "appointment",
        "note_creation",
        "task_creation",
    }:
        return

    repo = MemoryRepository(db)
    journal = await repo.get_or_create_journal(user_id, _today())
    intent = classification.get("intent", "general_chat")
    normalized = message.strip()

    journal.summary = _append_summary(journal.summary, normalized[:300])

    if intent == "emotional_checkin" or "emotional" in classification.get("categories", []):
        journal.mood_score = _mood_from_text(normalized)

    if intent in {"study_log", "study_plan"} or "study" in classification.get("categories", []):
        journal.study_summary = _append_summary(journal.study_summary, normalized)

    if intent == "appointment":
        journal.summary = _append_summary(journal.summary, f"Compromisso: {normalized}")

    if intent == "workout_log" or "workout" in classification.get("categories", []):
        journal.workout_summary = _append_summary(journal.workout_summary, normalized)

    if intent == "expense_log" or "finance" in classification.get("categories", []):
        journal.finance_summary = _append_summary(journal.finance_summary, normalized)

    if intent == "habit_log":
        journal.habit_summary = _append_summary(journal.habit_summary, normalized)

    events = dict(journal.important_events or {})
    events.setdefault("messages", [])
    if isinstance(events["messages"], list):
        events["messages"].append(
            {
                "intent": intent,
                "text": normalized[:200],
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )
    journal.important_events = events

    await db.flush()
    await db.refresh(journal)
