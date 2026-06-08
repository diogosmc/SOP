"""Merge duplicate memories using semantic similarity."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.modules.memory.models import AIMemory, MemoryType
from app.modules.memory.repository import MemoryRepository

MAX_COSINE_DISTANCE = 0.15


async def consolidate_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    candidates: list[dict],
    *,
    ollama: OllamaClient | None = None,
    max_distance: float = MAX_COSINE_DISTANCE,
) -> list[AIMemory]:
    """Persist memories, updating existing ones when semantically similar."""
    if not candidates:
        return []

    client = ollama or OllamaClient()
    repo = MemoryRepository(db)
    saved: list[AIMemory] = []

    for candidate in candidates:
        content = str(candidate.get("content", "")).strip()
        if not content:
            continue

        embedding = await client.embed(content)
        similar = await repo.find_similar(
            user_id, embedding, max_distance=max_distance, limit=1
        )

        mem_type = candidate.get("type", MemoryType.FACT.value)
        try:
            memory_type = MemoryType(mem_type)
        except ValueError:
            memory_type = MemoryType.FACT

        importance = candidate.get("importance", 5)
        confidence = candidate.get("confidence", 0.8)
        source = candidate.get("source")

        if similar:
            existing = similar[0]
            existing.content = content
            existing.type = memory_type
            existing.importance = max(existing.importance, int(importance))
            existing.confidence = max(existing.confidence, float(confidence))
            if source:
                existing.source = source
            existing.embedding = embedding
            await db.flush()
            await db.refresh(existing)
            saved.append(existing)
        else:
            memory = await repo.create(
                user_id,
                memory_type=memory_type,
                content=content,
                importance=int(importance),
                confidence=float(confidence),
                source=source,
                embedding=embedding,
            )
            saved.append(memory)

    return saved
