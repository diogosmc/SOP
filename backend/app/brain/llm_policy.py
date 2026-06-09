"""LLM usage policy for Telegram Conversation Brain."""

from __future__ import annotations

from app.brain.schedule_builder import is_tomorrow_list_request
from app.brain.schemas import ConversationContext
from app.brain.state_manager import is_ack_message

_FINANCE_KEYWORDS = ("gastei", "paguei", "comprei", "despesa", "gasto de", "r$", " reais")


def _has_finance_keyword(message: str) -> bool:
    lowered = message.lower()
    return any(kw in lowered for kw in _FINANCE_KEYWORDS)


def _is_explicit_command(message: str, primary: str) -> bool:
    """Only skip LLM for short, unambiguous action messages."""
    lowered = message.lower().strip()
    if primary == "expense_log":
        return _has_finance_keyword(message)
    if primary == "note_creation":
        return lowered.startswith(("anota ", "anotar ", "anota:", "anotar:"))
    if primary == "workout_log":
        return any(w in lowered for w in ("treinei", "malhei", "corri km", "vou treinar"))
    if primary == "study_log":
        return any(w in lowered for w in ("estudei", "revisei hoje", "estudei hoje"))
    return False


def should_use_llm(message: str, context: ConversationContext, mode: str) -> bool:
    """Decide whether to call Ollama for this Telegram message."""
    if context.is_ack or is_ack_message(message):
        return False

    if is_tomorrow_list_request(message):
        return False

    if mode == "fallback_only":
        return False
    if mode == "llm_only":
        return True

    primary = context.primary_intent or context.intent

    if _is_explicit_command(message, primary):
        return False

    return True
