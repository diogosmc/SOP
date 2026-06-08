"""LLM usage policy for Telegram Conversation Brain."""

from __future__ import annotations

from app.brain.schemas import ConversationContext
from app.brain.state_manager import is_ack_message

_FALLBACK_INTENTS = frozenset(
    {
        "expense_log",
        "note_creation",
        "task_creation",
        "workout_log",
        "study_log",
    }
)

_LLM_INTENTS = frozenset(
    {
        "emotional_checkin",
        "general_chat",
        "planning_request",
        "routine_planning",
        "question",
    }
)


def should_use_llm(message: str, context: ConversationContext, mode: str) -> bool:
    """Decide whether to call Ollama for this Telegram message."""
    if context.is_ack or is_ack_message(message):
        return False

    if mode == "fallback_only":
        return False
    if mode == "llm_only":
        return True

    primary = context.primary_intent or context.intent
    secondary = context.secondary_intents or []

    if primary in _FALLBACK_INTENTS and not secondary:
        return False

    if primary in _LLM_INTENTS:
        return True

    if secondary:
        return True

    if primary == "appointment" and "emotional_checkin" in secondary:
        return True

    if primary == "study_plan":
        return "emotional_checkin" in secondary

    return primary in {"general_chat", "question"}
