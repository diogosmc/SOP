"""Note service."""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.notes.repository import NoteRepository
from app.modules.notes.schemas import (
    ChunkSearchResult,
    IndexNoteResult,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)


class NoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = NoteRepository(db)

    async def create(self, user_id: uuid.UUID, data: NoteCreate) -> NoteResponse:
        note = await self.repo.create(user_id, data)
        return NoteResponse.model_validate(note)

    async def get(self, note_id: uuid.UUID, user_id: uuid.UUID) -> NoteResponse:
        note = await self.repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return NoteResponse.model_validate(note)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        tag: Optional[str] = None,
        favorite: Optional[bool] = None,
        archived: Optional[bool] = None,
    ) -> PaginatedResponse[NoteResponse]:
        items, total = await self.repo.list(
            user_id, tag, favorite, archived, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [NoteResponse.model_validate(n) for n in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def search(
        self,
        user_id: uuid.UUID,
        query_text: str,
        pagination: PaginationParams,
    ) -> PaginatedResponse[NoteResponse]:
        items, total = await self.repo.search(
            user_id, query_text, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [NoteResponse.model_validate(n) for n in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, note_id: uuid.UUID, user_id: uuid.UUID, data: NoteUpdate
    ) -> NoteResponse:
        note = await self.repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        updated = await self.repo.update(note, data)
        return NoteResponse.model_validate(updated)

    async def delete(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        note = await self.repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        await self.repo.delete(note)

    async def index_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> IndexNoteResult:
        from app.ai.rag.chunker import chunk_text
        from app.ai.rag.indexer import index_note as rag_index_note
        from sqlalchemy import func, select

        from app.modules.notes.models import DocumentChunk

        note = await self.repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

        document = await rag_index_note(note_id, user_id, self.repo.db)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note has no indexable content",
            )

        count_result = await self.repo.db.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
        )
        chunks_count = count_result.scalar_one()
        expected = len(chunk_text(f"{note.title}\n\n{note.content}".strip()))

        return IndexNoteResult(
            document_id=document.id,
            note_id=note_id,
            title=document.title,
            chunks_indexed=chunks_count if chunks_count else expected,
        )

    async def search_semantic(
        self, user_id: uuid.UUID, query: str, limit: int = 5
    ) -> List[ChunkSearchResult]:
        from app.ai.rag.searcher import search_chunks

        results = await search_chunks(query, user_id, self.repo.db, limit=limit)
        return [ChunkSearchResult.model_validate(item) for item in results]
