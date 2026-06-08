"""Tests for RAG semantic search."""

import pytest

from app.ai.rag.indexer import index_note
from app.ai.rag.searcher import search_chunks
from app.modules.notes.models import Note


async def _topic_embed(text: str) -> list[float]:
    vector = [0.0] * 768
    lowered = text.lower()
    if "loop" in lowered:
        vector[0] = 1.0
    elif "hábito" in lowered or "habito" in lowered:
        vector[1] = 1.0
    else:
        vector[2] = 1.0
    return vector


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_chunks_returns_similar_chunks(
    db_session, default_user_id
) -> None:
    loops_note = Note(
        user_id=default_user_id,
        title="Loops",
        content="For loops e while loops em Python são essenciais para iteração.",
    )
    habits_note = Note(
        user_id=default_user_id,
        title="Hábitos",
        content="Rotina matinal e hábitos diários para produtividade.",
    )
    db_session.add_all([loops_note, habits_note])
    await db_session.flush()

    await index_note(
        loops_note.id, default_user_id, db_session, embed_func=_topic_embed
    )
    await index_note(
        habits_note.id, default_user_id, db_session, embed_func=_topic_embed
    )

    results = await search_chunks(
        "o que eu anotei sobre loops?",
        default_user_id,
        db_session,
        limit=5,
        embed_func=_topic_embed,
    )

    assert results
    top = results[0]
    assert "loop" in top["content"].lower()
    assert top["source_type"] == "note"
    assert top["similarity"] > 0.0
    assert "chunk_id" in top
    assert "document_id" in top
    assert "source_id" in top
