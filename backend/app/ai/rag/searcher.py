"""Semantic search over document chunks via pgvector."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import ollama_embed
from app.modules.notes.models import Document, DocumentChunk

EmbedFunc = Callable[..., Any]


async def search_chunks(
    query: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 5,
    threshold: float = 0.0,
    embed_func: Optional[EmbedFunc] = None,
) -> list[dict[str, Any]]:
    """Embed the query and return the most similar document chunks."""
    embed = embed_func or ollama_embed
    normalized = query.strip()
    if not normalized:
        return []

    query_embedding = await embed(normalized)
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    stmt = (
        select(
            DocumentChunk,
            Document.source_type,
            Document.source_id,
            distance.label("distance"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    chunks: list[dict[str, Any]] = []
    for chunk, source_type, source_id, dist in rows:
        similarity = 1.0 - float(dist) if dist is not None else 0.0
        if similarity < threshold:
            continue
        chunks.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "similarity": round(similarity, 4),
                "source_type": source_type.value,
                "source_id": source_id,
            }
        )
    return chunks
