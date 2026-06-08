"""Orchestrate message classification, extraction, and memory persistence."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.classifier import classify_message
from app.ai.memory.consolidator import consolidate_memories
from app.ai.memory.extractor import extract_memories
from app.ai.ollama import OllamaClient
from app.modules.memory.models import AIMemory


async def process_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    text: str,
    *,
    ollama: OllamaClient | None = None,
) -> dict:
    """Classify a message, extract memories when relevant, and consolidate them."""
    client = ollama or OllamaClient()
    classification = await classify_message(text, client)

    saved: list[AIMemory] = []
    if classification.get("save_memory"):
        candidates = await extract_memories(text, classification, client)
        saved = await consolidate_memories(db, user_id, candidates, ollama=client)

    return {
        "classification": classification,
        "memories": [
            {
                "id": str(memory.id),
                "type": memory.type.value,
                "content": memory.content,
                "importance": memory.importance,
                "confidence": memory.confidence,
            }
            for memory in saved
        ],
    }
