"""Note API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.notes.schemas import NoteCreate, NoteResponse, NoteUpdate
from app.modules.notes.service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=APIResponse[NoteResponse])
async def create_note(
    data: NoteCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NoteResponse]:
    service = NoteService(db)
    return APIResponse(data=await service.create(user_id, data))


@router.get("", response_model=APIResponse)
async def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tag: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = NoteService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list(user_id, pagination, tag))


@router.get("/{note_id}", response_model=APIResponse[NoteResponse])
async def get_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NoteResponse]:
    service = NoteService(db)
    return APIResponse(data=await service.get(note_id, user_id))


@router.patch("/{note_id}", response_model=APIResponse[NoteResponse])
async def update_note(
    note_id: uuid.UUID,
    data: NoteUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NoteResponse]:
    service = NoteService(db)
    return APIResponse(data=await service.update(note_id, user_id, data))


@router.delete("/{note_id}", response_model=APIResponse[None])
async def delete_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = NoteService(db)
    await service.delete(note_id, user_id)
    return APIResponse(data=None)
