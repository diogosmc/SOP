"""Message intent classifier for natural-language Telegram input."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from app.ai.ollama import OllamaClient
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_INTENTS = frozenset(
    {
        "general_chat",
        "study_log",
        "workout_log",
        "expense_log",
        "habit_log",
        "task_creation",
        "goal_update",
        "emotional_checkin",
        "reminder_creation",
        "question",
    }
)

TOOL_INTENTS = frozenset(
    {
        "general_chat",
        "study_log",
        "workout_log",
        "expense_log",
        "habit_log",
        "task_creation",
    }
)

_KEYWORD_INTENTS: list[tuple[str, tuple[str, ...]]] = [
    ("expense_log", ("gastei", "paguei", "comprei", "reais", "r$", "despesa", "gasto")),
    ("workout_log", ("treinei", "treino", "academia", "corri", "musculação", "malhei")),
    ("study_log", ("estudei", "estudo", "li sobre", "aprendi", "revisei")),
    ("habit_log", ("hábito", "habito", "rotina", "acordei", "meditei", "bebi água")),
    ("task_creation", ("tarefa", "lembrar de", "preciso", "tenho que", "fazer")),
]

_AMOUNT_RE = re.compile(r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", re.IGNORECASE)


class ClassificationResult(BaseModel):
    intent: str = "general_chat"
    entities: dict[str, Any] = Field(default_factory=dict)
    actions: list[str] = Field(default_factory=list)
    save_memory: bool = True


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group())
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _keyword_classify(message: str) -> ClassificationResult:
    lowered = message.lower()
    intent = "general_chat"
    for candidate, keywords in _KEYWORD_INTENTS:
        if any(keyword in lowered for keyword in keywords):
            intent = candidate
            break

    entities: dict[str, Any] = {"raw_message": message}
    amount_match = _AMOUNT_RE.search(message)
    if amount_match and intent == "expense_log":
        entities["amount"] = float(amount_match.group(1).replace(",", "."))

    if intent == "task_creation":
        entities["title"] = message.strip()[:500]

    if intent in {"study_log", "workout_log"}:
        entities["notes"] = message.strip()

    return ClassificationResult(intent=intent, entities=entities, actions=[intent], save_memory=True)


def _normalize_result(data: dict[str, Any], message: str) -> ClassificationResult:
    intent = str(data.get("intent", "general_chat")).strip().lower()
    if intent not in SUPPORTED_INTENTS:
        intent = "general_chat"
    if intent not in TOOL_INTENTS:
        intent = "general_chat"

    entities = data.get("entities")
    if not isinstance(entities, dict):
        entities = {}

    entities.setdefault("raw_message", message)

    actions = data.get("actions")
    if not isinstance(actions, list):
        actions = [intent]

    save_memory = data.get("save_memory", True)
    if not isinstance(save_memory, bool):
        save_memory = True

    return ClassificationResult(
        intent=intent,
        entities=entities,
        actions=[str(a) for a in actions],
        save_memory=save_memory,
    )


async def classify_message(
    message: str,
    *,
    ollama: OllamaClient | None = None,
) -> ClassificationResult:
    """Classify a natural-language message into intent, entities, and actions."""
    text = message.strip()
    if not text:
        return ClassificationResult(intent="general_chat", entities={"raw_message": text})

    client = ollama or OllamaClient()
    settings = get_settings()
    prompt = f"""Classifique a mensagem abaixo. Retorne APENAS JSON válido, sem markdown:
{{
  "intent": "general_chat|study_log|workout_log|expense_log|habit_log|task_creation",
  "entities": {{}},
  "actions": [],
  "save_memory": true
}}

Extraia entidades úteis (amount, category, title, habit_name, duration_minutes, subject, notes).

Mensagem: {text}"""

    try:
        result = await client.generate(
            settings.ollama_fast_model,
            prompt,
            options={"temperature": 0.1},
        )
        content = str(result.get("response", ""))
        parsed = _extract_json(content)
        if parsed:
            return _normalize_result(parsed, text)
    except Exception as exc:
        logger.warning("classifier_ollama_failed", error=str(exc))

    return _keyword_classify(text)
