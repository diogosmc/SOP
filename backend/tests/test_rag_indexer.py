"""Tests for RAG note indexer."""

import pytest
from sqlalchemy import func, select

from app.ai.rag.indexer import index_note
from app.modules.notes.models import Document, DocumentChunk, DocumentSourceType, Note


async def _mock_embed(_text: str) -> list[float]:
    return [0.01] * 768


@pytest.mark.integration
@pytest.mark.asyncio
async def test_index_note_creates_document_and_chunks(
    db_session, default_user_id
) -> None:
    note = Note(
        user_id=default_user_id,
        title="Loops em Python",
        content=("For loops e while loops são fundamentais. " * 30).strip(),
    )
    db_session.add(note)
    await db_session.flush()

    document = await index_note(
        note.id, default_user_id, db_session, embed_func=_mock_embed
    )

    assert document is not None
    assert document.title == note.title
    assert document.source_type == DocumentSourceType.NOTE
    assert document.source_id == note.id

    doc_result = await db_session.execute(
        select(Document).where(Document.id == document.id)
    )
    assert doc_result.scalar_one_or_none() is not None

    count_result = await db_session.execute(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
    )
    assert count_result.scalar_one() >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reindex_removes_old_chunks(db_session, default_user_id) -> None:
    note = Note(
        user_id=default_user_id,
        title="Nota inicial",
        content=("Conteúdo original para indexação. " * 25).strip(),
    )
    db_session.add(note)
    await db_session.flush()

    document = await index_note(
        note.id, default_user_id, db_session, embed_func=_mock_embed
    )
    old_ids_result = await db_session.execute(
        select(DocumentChunk.id).where(DocumentChunk.document_id == document.id)
    )
    old_ids = set(old_ids_result.scalars().all())
    assert old_ids

    note.content = ("Conteúdo atualizado após edição da nota. " * 25).strip()
    await db_session.flush()

    refreshed = await index_note(
        note.id, default_user_id, db_session, embed_func=_mock_embed
    )
    assert refreshed is not None
    assert refreshed.id == document.id

    new_ids_result = await db_session.execute(
        select(DocumentChunk.id).where(DocumentChunk.document_id == document.id)
    )
    new_ids = set(new_ids_result.scalars().all())
    assert new_ids
    assert old_ids.isdisjoint(new_ids)
