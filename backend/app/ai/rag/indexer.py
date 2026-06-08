"""Index notes into document chunks with embeddings."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import ollama_embed
from app.ai.rag.chunker import chunk_text
from app.modules.notes.models import Document, DocumentChunk, DocumentSourceType, Note

EmbedFunc = Callable[..., Any]


async def index_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    embed_func: Optional[EmbedFunc] = None,
) -> Document | None:
    """Create or refresh a Document and its embedded chunks for a note."""
    embed = embed_func or ollama_embed

    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None

    full_text = f"{note.title}\n\n{note.content}".strip()
    if not full_text:
        return None

    existing = await db.execute(
        select(Document).where(
            Document.user_id == user_id,
            Document.source_type == DocumentSourceType.NOTE,
            Document.source_id == note_id,
        )
    )
    document = existing.scalar_one_or_none()

    if document:
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        document.title = note.title
        document.content = full_text
    else:
        document = Document(
            user_id=user_id,
            source_type=DocumentSourceType.NOTE,
            source_id=note_id,
            title=note.title,
            content=full_text,
        )
        db.add(document)
        await db.flush()

    text_chunks = chunk_text(full_text)
    for index, chunk_content in enumerate(text_chunks):
        embedding = await embed(chunk_content)
        db.add(
            DocumentChunk(
                document_id=document.id,
                user_id=user_id,
                chunk_index=index,
                content=chunk_content,
                embedding=embedding,
            )
        )

    await db.flush()
    await db.refresh(document)
    return document
