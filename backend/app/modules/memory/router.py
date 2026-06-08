"""Memory API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.memory.models import MemoryType
from app.modules.memory.schemas import (
    AIMemoryCreate,
    AIMemoryResponse,
    AIMemoryUpdate,
    AINoteCreate,
    AINoteResponse,
    DailyJournalResponse,
)
from app.modules.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/memories", response_model=APIResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[MemoryType] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = MemoryService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_memories(user_id, pagination, type))


@router.post("/memories", response_model=APIResponse[AIMemoryResponse])
async def create_memory(
    data: AIMemoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIMemoryResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.create_memory(user_id, data))


@router.put("/memories/{memory_id}", response_model=APIResponse[AIMemoryResponse])
async def update_memory(
    memory_id: uuid.UUID,
    data: AIMemoryUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIMemoryResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.update_memory(memory_id, user_id, data))


@router.delete("/memories/{memory_id}", response_model=APIResponse[None])
async def delete_memory(
    memory_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = MemoryService(db)
    await service.delete_memory(memory_id, user_id)
    return APIResponse(data=None)


@router.get("/notes", response_model=APIResponse)
async def list_ai_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = MemoryService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_ai_notes(user_id, pagination))


@router.post("/notes", response_model=APIResponse[AINoteResponse])
async def create_ai_note(
    data: AINoteCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AINoteResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.create_ai_note(user_id, data))


@router.delete("/notes/{note_id}", response_model=APIResponse[None])
async def delete_ai_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = MemoryService(db)
    await service.delete_ai_note(note_id, user_id)
    return APIResponse(data=None)


@router.get("/journal/today", response_model=APIResponse[DailyJournalResponse])
async def get_today_journal(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DailyJournalResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.get_today_journal(user_id))


@router.post("/journal/rebuild-today", response_model=APIResponse[DailyJournalResponse])
async def rebuild_today_journal(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DailyJournalResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.rebuild_today_journal(user_id))
