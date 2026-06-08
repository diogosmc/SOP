"""Memory, AI notes, and daily journal persistence."""

import uuid
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.models import AIMemory, AINote, DailyJournal, MemoryType
from app.modules.memory.schemas import AINoteCreate, AIMemoryUpdate


class MemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        *,
        memory_type: MemoryType,
        content: str,
        importance: int = 5,
        confidence: float = 0.8,
        source: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AIMemory:
        memory = AIMemory(
            user_id=user_id,
            type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            source=source,
            embedding=embedding,
            expires_at=expires_at,
        )
        self.db.add(memory)
        await self.db.flush()
        await self.db.refresh(memory)
        return memory

    async def get_by_id(
        self, memory_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[AIMemory]:
        result = await self.db.execute(
            select(AIMemory).where(AIMemory.id == memory_id, AIMemory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_memories(
        self,
        user_id: uuid.UUID,
        memory_type: Optional[MemoryType] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AIMemory], int]:
        query = select(AIMemory).where(AIMemory.user_id == user_id)
        count_query = (
            select(func.count()).select_from(AIMemory).where(AIMemory.user_id == user_id)
        )
        if memory_type:
            query = query.where(AIMemory.type == memory_type)
            count_query = count_query.where(AIMemory.type == memory_type)

        query = query.order_by(AIMemory.importance.desc(), AIMemory.updated_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, memory: AIMemory, data: AIMemoryUpdate) -> AIMemory:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(memory, key, value)
        await self.db.flush()
        await self.db.refresh(memory)
        return memory

    async def delete(self, memory: AIMemory) -> None:
        await self.db.delete(memory)
        await self.db.flush()

    async def create_ai_note(
        self, user_id: uuid.UUID, data: AINoteCreate
    ) -> AINote:
        note = AINote(user_id=user_id, **data.model_dump(mode="json"))
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def get_ai_note_by_id(
        self, note_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[AINote]:
        result = await self.db.execute(
            select(AINote).where(AINote.id == note_id, AINote.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_ai_notes(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AINote], int]:
        query = select(AINote).where(AINote.user_id == user_id)
        count_query = (
            select(func.count()).select_from(AINote).where(AINote.user_id == user_id)
        )
        query = query.order_by(AINote.importance.desc(), AINote.updated_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def delete_ai_note(self, note: AINote) -> None:
        await self.db.delete(note)
        await self.db.flush()

    async def get_journal_by_date(
        self, user_id: uuid.UUID, journal_date: date
    ) -> Optional[DailyJournal]:
        result = await self.db.execute(
            select(DailyJournal).where(
                DailyJournal.user_id == user_id,
                DailyJournal.date == journal_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_journal(
        self, user_id: uuid.UUID, journal_date: date
    ) -> DailyJournal:
        journal = await self.get_journal_by_date(user_id, journal_date)
        if journal:
            return journal
        journal = DailyJournal(user_id=user_id, date=journal_date, important_events={})
        self.db.add(journal)
        await self.db.flush()
        await self.db.refresh(journal)
        return journal
