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
    ProcessMessageRequest,
    ProcessMessageResponse,
)
from app.modules.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/process", response_model=APIResponse[ProcessMessageResponse])
async def process_message_endpoint(
    data: ProcessMessageRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProcessMessageResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.process_user_message(user_id, data.message))


@router.post("", response_model=APIResponse[AIMemoryResponse])
async def create_memory(
    data: AIMemoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIMemoryResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.create(user_id, data))


@router.get("", response_model=APIResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[MemoryType] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = MemoryService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list(user_id, pagination, type))


@router.get("/notes", response_model=APIResponse)
async def list_ai_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = MemoryService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_notes(user_id, pagination))


@router.get("/{memory_id}", response_model=APIResponse[AIMemoryResponse])
async def get_memory(
    memory_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIMemoryResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.get(memory_id, user_id))


@router.patch("/{memory_id}", response_model=APIResponse[AIMemoryResponse])
async def update_memory(
    memory_id: uuid.UUID,
    data: AIMemoryUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIMemoryResponse]:
    service = MemoryService(db)
    return APIResponse(data=await service.update(memory_id, user_id, data))


@router.delete("/{memory_id}", response_model=APIResponse[None])
async def delete_memory(
    memory_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = MemoryService(db)
    await service.delete(memory_id, user_id)
    return APIResponse(data=None)
