"""Habit API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.habits.models import HabitType
from app.modules.habits.schemas import HabitCreate, HabitResponse, HabitUpdate
from app.modules.habits.service import HabitService

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("", response_model=APIResponse[HabitResponse])
async def create_habit(
    data: HabitCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HabitResponse]:
    service = HabitService(db)
    return APIResponse(data=await service.create(user_id, data))


@router.get("", response_model=APIResponse)
async def list_habits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active: Optional[bool] = None,
    habit_type: Optional[HabitType] = Query(default=None, alias="type"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = HabitService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list(user_id, pagination, active, habit_type))


@router.get("/{habit_id}", response_model=APIResponse[HabitResponse])
async def get_habit(
    habit_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HabitResponse]:
    service = HabitService(db)
    return APIResponse(data=await service.get(habit_id, user_id))


@router.patch("/{habit_id}", response_model=APIResponse[HabitResponse])
async def update_habit(
    habit_id: uuid.UUID,
    data: HabitUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HabitResponse]:
    service = HabitService(db)
    return APIResponse(data=await service.update(habit_id, user_id, data))


@router.delete("/{habit_id}", response_model=APIResponse[None])
async def delete_habit(
    habit_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = HabitService(db)
    await service.delete(habit_id, user_id)
    return APIResponse(data=None)
