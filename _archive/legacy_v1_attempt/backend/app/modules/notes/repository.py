"""Note repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notes.models import Note
from app.modules.notes.schemas import NoteCreate, NoteUpdate


class NoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: NoteCreate, *, is_indexed: bool = False) -> Note:
        note = Note(user_id=user_id, is_indexed=is_indexed, **data.model_dump())
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def get_by_id(self, note_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Note]:
        result = await self.db.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        tag: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Note], int]:
        query = select(Note).where(Note.user_id == user_id)
        count_query = select(func.count()).select_from(Note).where(Note.user_id == user_id)
        if tag:
            query = query.where(Note.tags.contains([tag]))
            count_query = count_query.where(Note.tags.contains([tag]))
        query = query.order_by(Note.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(
        self, note: Note, data: NoteUpdate, *, is_indexed: Optional[bool] = None
    ) -> Note:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(note, field, value)
        if is_indexed is not None:
            note.is_indexed = is_indexed
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def delete(self, note: Note) -> None:
        await self.db.delete(note)
        await self.db.flush()
