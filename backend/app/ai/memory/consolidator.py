"""Merge memory candidates avoiding duplicates via simple text similarity."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.models import AIMemory, MemoryType
from app.modules.memory.repository import MemoryRepository

SIMILARITY_THRESHOLD = 0.45
_EMOTIONAL_MAX_CONFIDENCE = 0.5
_EMOTIONAL_EXPIRY_DAYS = 7


def _normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", lowered))


def _keyword_set(text: str) -> set[str]:
    words = _normalize_text(text).split()
    return {word for word in words if len(word) > 3}


def text_similarity(left: str, right: str) -> float:
    """Simple Jaccard similarity over meaningful words."""
    left_words = _keyword_set(left)
    right_words = _keyword_set(right)
    if not left_words or not right_words:
        return 0.0
    intersection = left_words & right_words
    union = left_words | right_words
    return len(intersection) / len(union)


def find_similar_memory(
    existing_memories: list[AIMemory], candidate: dict[str, Any]
) -> AIMemory | None:
    """Find an existing memory similar enough to update instead of creating."""
    candidate_type = candidate.get("type")
    candidate_content = str(candidate.get("content", "")).strip()
    if not candidate_content:
        return None

    best: AIMemory | None = None
    best_score = 0.0

    for memory in existing_memories:
        if memory.type.value != candidate_type:
            continue
        score = text_similarity(memory.content, candidate_content)
        if score >= SIMILARITY_THRESHOLD and score > best_score:
            best = memory
            best_score = score

    return best


async def consolidate_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    candidates: list[dict[str, Any]],
) -> list[AIMemory]:
    """Persist memories, updating similar ones instead of duplicating."""
    if not candidates:
        return []

    repo = MemoryRepository(db)
    existing, _ = await repo.list_memories(user_id, offset=0, limit=500)
    saved: list[AIMemory] = []

    for candidate in candidates:
        content = str(candidate.get("content", "")).strip()
        if not content:
            continue

        mem_type_str = str(candidate.get("type", MemoryType.FACT.value))
        try:
            memory_type = MemoryType(mem_type_str)
        except ValueError:
            memory_type = MemoryType.FACT

        importance = max(1, min(10, int(candidate.get("importance", 5))))
        confidence = max(0.0, min(1.0, float(candidate.get("confidence", 0.8))))
        source = candidate.get("source", "chat")

        expires_at = candidate.get("expires_at")
        if memory_type == MemoryType.EMOTIONAL or candidate.get("temporary"):
            confidence = min(confidence, _EMOTIONAL_MAX_CONFIDENCE)
            if expires_at is None:
                expires_at = datetime.now(timezone.utc) + timedelta(days=_EMOTIONAL_EXPIRY_DAYS)

        similar = find_similar_memory(existing, candidate)
        if similar:
            similar.content = content
            similar.type = memory_type
            similar.importance = max(similar.importance, importance)
            similar.confidence = max(similar.confidence, confidence)
            similar.source = str(source) if source else similar.source
            if expires_at is not None:
                similar.expires_at = expires_at
            await db.flush()
            await db.refresh(similar)
            saved.append(similar)
            continue

        memory = await repo.create(
            user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            source=str(source) if source else None,
            expires_at=expires_at,
        )
        existing.append(memory)
        saved.append(memory)

    return saved
