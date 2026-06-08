"""Semantic search over document chunks via pgvector."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.core.config import get_settings
from app.modules.notes.models import Document, DocumentChunk


async def search_chunks(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
    *,
    ollama: OllamaClient | None = None,
) -> list[dict]:
    """Embed the query and return the most similar document chunks."""
    settings = get_settings()
    top_k = top_k if top_k is not None else settings.rag_top_k

    query = query.strip()
    if not query:
        return []

    client = ollama or OllamaClient()
    query_embedding = await client.embed(query)

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(
            DocumentChunk,
            Document.title,
            distance.label("distance"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(top_k)
    )

    result = await db.execute(stmt)
    rows = result.all()

    chunks: list[dict] = []
    for chunk, title, dist in rows:
        score = 1.0 - float(dist) if dist is not None else 0.0
        chunks.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "title": title,
                "score": score,
            }
        )
    return chunks
