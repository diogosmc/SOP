"""Memory business logic."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.classifier import classify_message
from app.ai.memory.consolidator import consolidate_memories
from app.ai.memory.extractor import extract_memory_candidates
from app.ai.memory.journal import update_daily_journal_from_message
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.memory.models import MemoryType
from app.modules.memory.repository import MemoryRepository
from app.modules.memory.schemas import (
    AIMemoryCreate,
    AIMemoryResponse,
    AIMemoryUpdate,
    AINoteCreate,
    AINoteResponse,
    DailyJournalResponse,
)

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MemoryRepository(db)

    async def process_chat_message(self, user_id: uuid.UUID, message: str) -> None:
        """Best-effort memory pipeline after chat; errors are logged, not raised."""
        classification = classify_message(message)
        candidates = extract_memory_candidates(message, classification)
        if candidates:
            await consolidate_memories(self.db, user_id, candidates)
        await update_daily_journal_from_message(user_id, message, classification, self.db)

    async def create_memory(
        self, user_id: uuid.UUID, data: AIMemoryCreate
    ) -> AIMemoryResponse:
        memory = await self.repo.create(
            user_id,
            memory_type=data.type,
            content=data.content,
            importance=data.importance,
            confidence=data.confidence,
            source=data.source,
            expires_at=data.expires_at,
        )
        return AIMemoryResponse.model_validate(memory)

    async def list_memories(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        memory_type: Optional[MemoryType] = None,
    ) -> PaginatedResponse[AIMemoryResponse]:
        items, total = await self.repo.list_memories(
            user_id, memory_type, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [AIMemoryResponse.model_validate(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_memory(
        self, memory_id: uuid.UUID, user_id: uuid.UUID, data: AIMemoryUpdate
    ) -> AIMemoryResponse:
        memory = await self.repo.get_by_id(memory_id, user_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        updated = await self.repo.update(memory, data)
        return AIMemoryResponse.model_validate(updated)

    async def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> None:
        memory = await self.repo.get_by_id(memory_id, user_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        await self.repo.delete(memory)

    async def create_ai_note(
        self, user_id: uuid.UUID, data: AINoteCreate
    ) -> AINoteResponse:
        note = await self.repo.create_ai_note(user_id, data)
        return AINoteResponse.model_validate(note)

    async def list_ai_notes(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[AINoteResponse]:
        items, total = await self.repo.list_ai_notes(
            user_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [AINoteResponse.model_validate(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def delete_ai_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        note = await self.repo.get_ai_note_by_id(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="AI note not found"
            )
        await self.repo.delete_ai_note(note)

    async def get_today_journal(self, user_id: uuid.UUID) -> DailyJournalResponse:
        today = datetime.now(timezone.utc).date()
        journal = await self.repo.get_or_create_journal(user_id, today)
        return DailyJournalResponse.model_validate(journal)

    async def rebuild_today_journal(self, user_id: uuid.UUID) -> DailyJournalResponse:
        today = datetime.now(timezone.utc).date()
        journal = await self.repo.get_or_create_journal(user_id, today)

        memories, _ = await self.repo.list_memories(user_id, offset=0, limit=500)
        today_memories = [
            memory
            for memory in memories
            if memory.created_at.date() == today or memory.updated_at.date() == today
        ]

        journal.summary = None
        journal.study_summary = None
        journal.workout_summary = None
        journal.finance_summary = None
        journal.habit_summary = None
        journal.important_events = {"rebuilt_at": datetime.now(timezone.utc).isoformat()}

        for memory in today_memories:
            classification = {
                "intent": "general_chat",
                "categories": [memory.type.value],
                "should_save_memory": True,
            }
            if memory.type == MemoryType.STUDY:
                classification["intent"] = "study_log"
            elif memory.type == MemoryType.WORKOUT:
                classification["intent"] = "workout_log"
            elif memory.type == MemoryType.FINANCIAL:
                classification["intent"] = "expense_log"
            elif memory.type == MemoryType.EMOTIONAL:
                classification["intent"] = "emotional_checkin"
            elif memory.type == MemoryType.HABIT:
                classification["intent"] = "habit_log"
            elif memory.type == MemoryType.GOAL:
                classification["intent"] = "goal_update"

            await update_daily_journal_from_message(
                user_id, memory.content, classification, self.db
            )

        await self.db.refresh(journal)
        return DailyJournalResponse.model_validate(journal)
