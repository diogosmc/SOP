"""Build LLM context strings from retrieved RAG chunks."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.searcher import search_chunks


async def build_rag_context(
    query: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 5,
) -> str:
    """Return a short context string from the most relevant chunks."""
    chunks = await search_chunks(query, user_id, db, limit=limit)
    if not chunks:
        return ""

    selected = chunks[: min(limit, 5)]
    parts: list[str] = []
    for index, chunk in enumerate(selected, start=1):
        content = chunk.get("content", "").strip()
        if not content:
            continue
        parts.append(f"[{index}] {content}")

    if not parts:
        return ""

    return "Contexto relevante das suas notas:\n" + "\n\n".join(parts)
