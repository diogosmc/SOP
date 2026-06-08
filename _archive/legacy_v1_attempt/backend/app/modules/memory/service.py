"""Memory business logic."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.processor import process_message
from app.ai.ollama import OllamaClient
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.memory.models import MemoryType
from app.modules.memory.repository import MemoryRepository
from app.modules.memory.schemas import (
    AIMemoryCreate,
    AIMemoryResponse,
    AIMemoryUpdate,
    AINoteResponse,
    ProcessMessageResponse,
)


class MemoryService:
    def __init__(self, db: AsyncSession, ollama: Optional[OllamaClient] = None) -> None:
        self.repo = MemoryRepository(db)
        self.ollama = ollama or OllamaClient()

    async def create(
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

    async def get(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> AIMemoryResponse:
        memory = await self.repo.get_by_id(memory_id, user_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        return AIMemoryResponse.model_validate(memory)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        memory_type: Optional[MemoryType] = None,
    ) -> PaginatedResponse[AIMemoryResponse]:
        items, total = await self.repo.list_memories(
            user_id, memory_type, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [AIMemoryResponse.model_validate(m) for m in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, memory_id: uuid.UUID, user_id: uuid.UUID, data: AIMemoryUpdate
    ) -> AIMemoryResponse:
        memory = await self.repo.get_by_id(memory_id, user_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        updated = await self.repo.update(
            memory, **data.model_dump(exclude_unset=True)
        )
        return AIMemoryResponse.model_validate(updated)

    async def delete(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> None:
        memory = await self.repo.get_by_id(memory_id, user_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        await self.repo.delete(memory)

    async def list_notes(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[AINoteResponse]:
        items, total = await self.repo.list_ai_notes(
            user_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [AINoteResponse.model_validate(n) for n in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def process_user_message(
        self, user_id: uuid.UUID, message: str
    ) -> ProcessMessageResponse:
        result = await process_message(
            self.repo.db, user_id, message, ollama=self.ollama
        )
        return ProcessMessageResponse.model_validate(result)
