"""Select relevant memories for conversation context."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.schemas import MemorySnippet
from app.core.config import get_settings
from app.modules.memory.models import AIMemory, MemoryType

_TYPE_CATEGORY = {
    MemoryType.GOAL: "goals",
    MemoryType.PREFERENCE: "permanent",
    MemoryType.HABIT: "routine",
    MemoryType.PATTERN: "permanent",
    MemoryType.STUDY: "study",
    MemoryType.WORKOUT: "routine",
    MemoryType.FINANCIAL: "recent",
    MemoryType.EMOTIONAL: "emotional",
    MemoryType.ROUTINE: "routine",
    MemoryType.FACT: "permanent",
    MemoryType.OTHER: "recent",
}

_EMOTIONAL_WORDS = ("desanimado", "triste", "ansioso", "cansado", "culpado", "deitado")
_STUDY_WORDS = ("estud", "revisar", "prova", "faculdade", "matéria", "materia", "anatomia")
_GOAL_WORDS = ("objetivo", "meta", "quero passar", "medicina")


def _text_overlap_score(message: str, content: str) -> float:
    msg_tokens = {t for t in message.lower().split() if len(t) > 3}
    content_tokens = {t for t in content.lower().split() if len(t) > 3}
    if not msg_tokens or not content_tokens:
        return 0.0
    overlap = len(msg_tokens & content_tokens)
    return overlap / max(len(msg_tokens), 1)


def _intent_type_boost(message: str, memory_type: MemoryType) -> float:
    lowered = message.lower()
    if any(w in lowered for w in _EMOTIONAL_WORDS) and memory_type == MemoryType.EMOTIONAL:
        return 2.0
    if any(w in lowered for w in _STUDY_WORDS) and memory_type == MemoryType.STUDY:
        return 2.0
    if any(w in lowered for w in _GOAL_WORDS) and memory_type == MemoryType.GOAL:
        return 2.0
    return 0.0


async def select_relevant_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    limit: int | None = None,
) -> list[MemorySnippet]:
    settings = get_settings()
    max_items = limit or settings.brain_memory_limit

    result = await db.execute(
        select(AIMemory)
        .where(AIMemory.user_id == user_id)
        .order_by(AIMemory.importance.desc(), AIMemory.updated_at.desc())
        .limit(max_items * 4)
    )
    memories: Sequence[AIMemory] = result.scalars().all()

    scored: list[tuple[float, AIMemory]] = []
    for memory in memories:
        overlap = _text_overlap_score(message, memory.content)
        boost = _intent_type_boost(message, memory.type)
        score = memory.importance + overlap * 3 + boost + memory.confidence
        scored.append((score, memory))

    scored.sort(key=lambda item: item[0], reverse=True)
    snippets: list[MemorySnippet] = []
    seen: set[str] = set()
    for _, memory in scored[:max_items]:
        key = memory.content[:80]
        if key in seen:
            continue
        seen.add(key)
        snippets.append(
            MemorySnippet(
                content=memory.content[:400],
                memory_type=memory.type.value,
                importance=memory.importance,
                category=_TYPE_CATEGORY.get(memory.type, "recent"),
            )
        )
    return snippets


async def select_important_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 5,
) -> list[MemorySnippet]:
    result = await db.execute(
        select(AIMemory)
        .where(AIMemory.user_id == user_id, AIMemory.importance >= 7)
        .order_by(AIMemory.importance.desc(), AIMemory.updated_at.desc())
        .limit(limit)
    )
    memories = result.scalars().all()
    goal_result = await db.execute(
        select(AIMemory)
        .where(AIMemory.user_id == user_id, AIMemory.type == MemoryType.GOAL)
        .order_by(AIMemory.importance.desc())
        .limit(1)
    )
    goal = goal_result.scalar_one_or_none()

    snippets: list[MemorySnippet] = []
    if goal:
        snippets.append(
            MemorySnippet(
                content=goal.content[:400],
                memory_type=goal.type.value,
                importance=goal.importance,
                category="goals",
            )
        )
    for memory in memories:
        if goal and memory.id == goal.id:
            continue
        snippets.append(
            MemorySnippet(
                content=memory.content[:400],
                memory_type=memory.type.value,
                importance=memory.importance,
                category=_TYPE_CATEGORY.get(memory.type, "permanent"),
            )
        )
        if len(snippets) >= limit:
            break
    return snippets[:limit]
