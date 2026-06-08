"""Batch embedding job for unindexed notes."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.ai.ollama import OllamaClient
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.modules.notes.models import Note

logger = get_logger(__name__)

BATCH_SIZE = 20


async def process_unindexed_notes() -> None:
    """Embed notes with is_indexed=false and mark them indexed."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)
    client = OllamaClient()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Note)
            .where(Note.user_id == user_id, Note.is_indexed.is_(False))
            .order_by(Note.updated_at.asc())
            .limit(BATCH_SIZE)
        )
        notes = list(result.scalars().all())
        if not notes:
            return

        indexed = 0
        for note in notes:
            text = f"{note.title}\n{note.content}".strip()
            if not text:
                note.is_indexed = True
                indexed += 1
                continue

            try:
                await client.embed(text)
                note.is_indexed = True
                indexed += 1
            except Exception as exc:
                logger.warning(
                    "note_embedding_failed",
                    note_id=str(note.id),
                    error=str(exc),
                )

        await db.commit()
        logger.info("notes_indexed_batch", count=indexed, batch_size=len(notes))
