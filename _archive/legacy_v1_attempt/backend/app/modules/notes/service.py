"""Note service."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.notes.repository import NoteRepository
from app.modules.notes.schemas import NoteCreate, NoteResponse, NoteUpdate


class NoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = NoteRepository(db)

    async def create(self, user_id: uuid.UUID, data: NoteCreate) -> NoteResponse:
        note = await self.repo.create(user_id, data, is_indexed=False)
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
    ) -> PaginatedResponse[NoteResponse]:
        items, total = await self.repo.list(user_id, tag, pagination.offset, pagination.page_size)
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
        updated = await self.repo.update(note, data, is_indexed=False)
        return NoteResponse.model_validate(updated)

    async def delete(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        note = await self.repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        await self.repo.delete(note)
