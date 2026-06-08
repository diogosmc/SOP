"""Rule-based memory candidate extraction."""

from __future__ import annotations

import re
from typing import Any

_GOAL_RE = re.compile(
    r"(?:quero passar em|quero ser|meu objetivo é|meu objetivo e|meta de|pretendo)\s+(.+)",
    re.IGNORECASE,
)
_STUDY_DIFFICULTY_RE = re.compile(
    r"dificuldade em\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_WORKOUT_PREF_RE = re.compile(
    r"treino melhor (?:de|pela|no|na)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_EXPENSE_RE = re.compile(
    r"(?:gastei|paguei|comprei)\s+(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)\s*(?:no|na|em|com)?\s*(.+?)(?:\.|$)?",
    re.IGNORECASE,
)

_EMOTIONAL_KEYWORDS = (
    "desanimado",
    "desanimada",
    "triste",
    "ansioso",
    "ansiosa",
    "estressado",
    "estressada",
    "cansado",
    "cansada",
)


def extract_memory_candidates(text: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract durable or temporary memory candidates from a classified message."""
    if not classification.get("should_save_memory"):
        return []

    normalized = text.strip()
    if not normalized:
        return []

    intent = classification.get("intent", "general_chat")
    candidates: list[dict[str, Any]] = []

    goal_match = _GOAL_RE.search(normalized)
    if goal_match or intent == "goal_update":
        target = (goal_match.group(1) if goal_match else normalized).strip(" .")
        if target:
            candidates.append(
                {
                    "type": "goal",
                    "content": f"Objetivo do usuário: passar ou alcançar {target}",
                    "importance": 8,
                    "confidence": 0.85,
                    "source": "chat",
                }
            )

    study_match = _STUDY_DIFFICULTY_RE.search(normalized)
    if study_match or (intent == "study_log" and "dificuldade" in normalized.lower()):
        subject = (study_match.group(1) if study_match else "estudos").strip(" .")
        candidates.append(
            {
                "type": "study",
                "content": f"Dificuldade em estudos: {subject}",
                "importance": 6,
                "confidence": 0.75,
                "source": "chat",
            }
        )
    elif intent == "study_log":
        candidates.append(
            {
                "type": "study",
                "content": f"Registro de estudo: {normalized}",
                "importance": 5,
                "confidence": 0.7,
                "source": "chat",
            }
        )

    workout_pref = _WORKOUT_PREF_RE.search(normalized)
    if workout_pref:
        period = workout_pref.group(1).strip(" .")
        candidates.append(
            {
                "type": "preference",
                "content": f"Prefere treinar {period}",
                "importance": 6,
                "confidence": 0.8,
                "source": "chat",
            }
        )
    elif intent == "workout_log":
        candidates.append(
            {
                "type": "workout",
                "content": f"Registro de treino: {normalized}",
                "importance": 5,
                "confidence": 0.75,
                "source": "chat",
            }
        )

    expense_match = _EXPENSE_RE.search(normalized)
    if expense_match or intent == "expense_log":
        amount = classification.get("entities", {}).get("amount")
        if expense_match:
            amount = float(expense_match.group(1).replace(",", "."))
            description = expense_match.group(2).strip(" .") or "despesa"
        else:
            description = "despesa"
        amount_text = f"R$ {amount:.2f}" if amount is not None else "valor não informado"
        candidates.append(
            {
                "type": "financial",
                "content": f"Gasto registrado: {amount_text} em {description}",
                "importance": 5,
                "confidence": 0.8,
                "source": "chat",
            }
        )

    if intent == "emotional_checkin" or any(k in normalized.lower() for k in _EMOTIONAL_KEYWORDS):
        candidates.append(
            {
                "type": "emotional",
                "content": f"Contexto emocional temporário: {normalized}",
                "importance": 4,
                "confidence": 0.4,
                "source": "chat",
                "temporary": True,
            }
        )

    if intent == "habit_log":
        candidates.append(
            {
                "type": "habit",
                "content": f"Hábito ou rotina: {normalized}",
                "importance": 5,
                "confidence": 0.7,
                "source": "chat",
            }
        )

    return _dedupe_candidates(candidates)


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for candidate in candidates:
        key = (candidate["type"], candidate["content"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique
