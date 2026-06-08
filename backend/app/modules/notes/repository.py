"""Note repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notes.models import Note
from app.modules.notes.schemas import NoteCreate, NoteUpdate


class NoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: NoteCreate) -> Note:
        note = Note(user_id=user_id, **data.model_dump(mode="json"))
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
        favorite: Optional[bool] = None,
        archived: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Note], int]:
        query = select(Note).where(Note.user_id == user_id)
        count_query = select(func.count()).select_from(Note).where(Note.user_id == user_id)
        if tag is not None:
            query = query.where(Note.tags.contains([tag]))
            count_query = count_query.where(Note.tags.contains([tag]))
        if favorite is not None:
            query = query.where(Note.favorite == favorite)
            count_query = count_query.where(Note.favorite == favorite)
        if archived is not None:
            query = query.where(Note.archived == archived)
            count_query = count_query.where(Note.archived == archived)
        query = query.order_by(Note.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def search(
        self,
        user_id: uuid.UUID,
        query_text: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Note], int]:
        pattern = f"%{query_text}%"
        filters = (
            Note.user_id == user_id,
            or_(Note.title.ilike(pattern), Note.content.ilike(pattern)),
        )
        query = (
            select(Note)
            .where(*filters)
            .order_by(Note.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(Note).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, note: Note, data: NoteUpdate) -> Note:
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(note, field, value)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def delete(self, note: Note) -> None:
        await self.db.delete(note)
        await self.db.flush()
