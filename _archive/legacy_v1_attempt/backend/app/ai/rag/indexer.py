"""Index notes into document chunks with embeddings."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.ai.rag.chunker import chunk_text
from app.modules.notes.models import Document, DocumentChunk, DocumentSourceType, Note


async def index_note(
    db: AsyncSession,
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    ollama: OllamaClient | None = None,
) -> Document | None:
    """Create or refresh a Document and its embedded chunks for a note."""
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None

    client = ollama or OllamaClient()
    full_text = f"{note.title}\n\n{note.content}".strip()
    content_hash = hashlib.sha256(full_text.encode()).hexdigest()

    existing = await db.execute(
        select(Document).where(
            Document.user_id == user_id,
            Document.source_type == DocumentSourceType.NOTE,
            Document.source_id == note_id,
        )
    )
    document = existing.scalar_one_or_none()

    if document and document.content_hash == content_hash:
        note.is_indexed = True
        await db.flush()
        return document

    if document:
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        document.title = note.title
        document.content_hash = content_hash
    else:
        document = Document(
            user_id=user_id,
            source_type=DocumentSourceType.NOTE,
            source_id=note_id,
            title=note.title,
            content_hash=content_hash,
        )
        db.add(document)
        await db.flush()

    chunks = chunk_text(full_text)
    for index, chunk_content in enumerate(chunks):
        embedding = await client.embed(chunk_content)
        db.add(
            DocumentChunk(
                document_id=document.id,
                user_id=user_id,
                chunk_index=index,
                content=chunk_content,
                embedding=embedding,
            )
        )

    note.is_indexed = True
    await db.flush()
    await db.refresh(document)
    return document
