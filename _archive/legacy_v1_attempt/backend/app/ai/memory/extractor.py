"""Extract durable memories from classified messages."""

from __future__ import annotations

import json

from app.ai.ollama import OllamaClient, OllamaError
from app.core.config import get_settings
from app.core.logging import get_logger
from app.modules.memory.models import MemoryType

logger = get_logger(__name__)

VALID_MEMORY_TYPES = {t.value for t in MemoryType}

EXTRACTOR_SYSTEM = """Você extrai memórias duráveis sobre o usuário do COPILOTO.
Responda APENAS com JSON válido: {"memories": [...]}

Cada memória deve ter:
- type: goal, preference, habit, pattern, study, workout, financial, emotional, routine, fact
- content: frase clara em português, em terceira pessoa sobre o usuário
- importance: inteiro 1-10
- confidence: float 0.0-1.0

Extraia apenas informações pessoais úteis e duráveis. Se não houver nada relevante, retorne {"memories": []}."""


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _intent_to_memory_type(intent: str) -> str:
    mapping = {
        "goal_update": MemoryType.GOAL.value,
        "study_log": MemoryType.STUDY.value,
        "workout_log": MemoryType.WORKOUT.value,
        "expense_log": MemoryType.FINANCIAL.value,
        "habit_log": MemoryType.HABIT.value,
        "emotional_checkin": MemoryType.EMOTIONAL.value,
    }
    return mapping.get(intent, MemoryType.FACT.value)


async def extract_memories(
    text: str,
    classification: dict,
    ollama: OllamaClient | None = None,
) -> list[dict]:
    """Derive memory candidates from a classified user message."""
    if not classification.get("save_memory"):
        return []

    text = text.strip()
    if not text:
        return []

    settings = get_settings()
    client = ollama or OllamaClient()
    intent = classification.get("intent", "general_chat")
    entities = classification.get("entities", {})

    prompt = (
        f"Mensagem:\n{text}\n\n"
        f"Intenção detectada: {intent}\n"
        f"Entidades: {json.dumps(entities, ensure_ascii=False)}"
    )

    try:
        result = await client.generate(
            settings.ollama_fast_model,
            prompt,
            system=EXTRACTOR_SYSTEM,
            options={"temperature": 0.2},
        )
        raw = result.get("response", "")
        if not isinstance(raw, str) or not raw.strip():
            return []

        parsed = _parse_json_response(raw)
        raw_memories = parsed.get("memories", [])
        if not isinstance(raw_memories, list):
            return []

        memories: list[dict] = []
        for item in raw_memories:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            if not content:
                continue

            mem_type = str(item.get("type", _intent_to_memory_type(intent)))
            if mem_type not in VALID_MEMORY_TYPES:
                mem_type = _intent_to_memory_type(intent)

            importance = item.get("importance", 5)
            confidence = item.get("confidence", 0.8)
            try:
                importance = max(1, min(10, int(importance)))
            except (TypeError, ValueError):
                importance = 5
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = 0.8

            memories.append(
                {
                    "type": mem_type,
                    "content": content,
                    "importance": importance,
                    "confidence": confidence,
                    "source": intent,
                }
            )
        return memories
    except (OllamaError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("extract_memories_failed", error=str(exc))
        return []
