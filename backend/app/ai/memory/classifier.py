"""Rule-based message classifier for evolutionary memory."""

from __future__ import annotations

import re
from typing import Any

_AMOUNT_RE = re.compile(r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", re.IGNORECASE)

_TRIVIAL_EXACT = frozenset(
    {
        "oi",
        "olá",
        "ola",
        "ok",
        "okay",
        "obrigado",
        "obrigada",
        "tchau",
        "valeu",
        "bom dia",
        "boa noite",
        "boa tarde",
        "sim",
        "não",
        "nao",
    }
)

_KEYWORD_RULES: list[tuple[str, tuple[str, ...], list[str]]] = [
    (
        "goal_update",
        ("quero passar", "meu objetivo", "meta de", "pretendo", "quero ser", "sonho em"),
        ["goal"],
    ),
    (
        "expense_log",
        ("gastei", "paguei", "comprei", "despesa", "gasto de", "r$", " reais"),
        ["finance"],
    ),
    (
        "workout_log",
        ("treinei", "treino", "academia", "corri", "malhei", "musculação", "musculacao"),
        ["workout"],
    ),
    (
        "study_log",
        (
            "estudei",
            "estudo",
            "dificuldade em",
            "aprendi",
            "revisei",
            "matéria",
            "materia",
            "física",
            "fisica",
            "matemática",
            "matematica",
        ),
        ["study"],
    ),
    (
        "emotional_checkin",
        (
            "desanimado",
            "triste",
            "ansioso",
            "ansiosa",
            "estressado",
            "estressada",
            "cansado hoje",
            "cansada hoje",
            "me sinto",
            "estou mal",
            "motivação baixa",
            "motivacao baixa",
        ),
        ["emotional"],
    ),
    (
        "habit_log",
        ("hábito", "habito", "rotina matinal", "meditei", "bebi água", "bebi agua"),
        ["habit", "routine"],
    ),
    (
        "task_creation",
        ("preciso fazer", "tenho que", "lembrar de", "criar tarefa", "nova tarefa"),
        ["routine"],
    ),
    (
        "reminder_creation",
        ("me avise", "me lembre", "lembrar de", "agendar"),
        ["routine"],
    ),
]


def _base_result() -> dict[str, Any]:
    return {
        "intent": "general_chat",
        "categories": [],
        "entities": {},
        "should_save_memory": True,
        "should_create_note": False,
        "requires_confirmation": False,
    }


def _is_trivial(text: str, lowered: str) -> bool:
    if not text:
        return True
    if lowered in _TRIVIAL_EXACT:
        return True
    if len(text) < 12 and "?" not in text:
        return True
    return False


def classify_message(text: str) -> dict[str, Any]:
    """Classify a user message using simple keyword rules."""
    normalized = text.strip()
    lowered = normalized.lower()
    result = _base_result()

    if _is_trivial(normalized, lowered):
        result["should_save_memory"] = False
        return result

    result["entities"]["raw_message"] = normalized

    for intent, keywords, categories in _KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            result["intent"] = intent
            result["categories"] = categories
            break

    if result["intent"] == "general_chat" and normalized.endswith("?"):
        result["intent"] = "question"
        result["should_save_memory"] = False

    amount_match = _AMOUNT_RE.search(normalized)
    if amount_match and result["intent"] in {"expense_log", "general_chat"}:
        if result["intent"] == "general_chat":
            result["intent"] = "expense_log"
            result["categories"] = ["finance"]
        result["entities"]["amount"] = float(amount_match.group(1).replace(",", "."))

    if result["intent"] == "goal_update":
        result["requires_confirmation"] = False

    if result["intent"] in {"task_creation", "reminder_creation"}:
        result["requires_confirmation"] = True
        result["should_save_memory"] = False

    if result["intent"] == "emotional_checkin":
        result["should_create_note"] = False

    if result["intent"] == "general_chat":
        result["should_save_memory"] = False

    return result
