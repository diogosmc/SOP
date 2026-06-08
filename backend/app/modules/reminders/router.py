"""Reminder API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.reminders.models import ReminderStatus
from app.modules.reminders.schemas import ReminderCreate, ReminderResponse, ReminderUpdate
from app.modules.reminders.service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=APIResponse)
async def list_reminders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ReminderStatus] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = ReminderService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list(user_id, pagination, status))


@router.post("", response_model=APIResponse[ReminderResponse])
async def create_reminder(
    data: ReminderCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReminderResponse]:
    service = ReminderService(db)
    return APIResponse(data=await service.create(user_id, data))


@router.put("/{reminder_id}", response_model=APIResponse[ReminderResponse])
async def update_reminder(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReminderResponse]:
    service = ReminderService(db)
    return APIResponse(data=await service.update(reminder_id, user_id, data))


@router.delete("/{reminder_id}", response_model=APIResponse[None])
async def delete_reminder(
    reminder_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = ReminderService(db)
    await service.delete(reminder_id, user_id)
    return APIResponse(data=None)


@router.post("/{reminder_id}/cancel", response_model=APIResponse[ReminderResponse])
async def cancel_reminder(
    reminder_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReminderResponse]:
    service = ReminderService(db)
    return APIResponse(data=await service.cancel(reminder_id, user_id))
