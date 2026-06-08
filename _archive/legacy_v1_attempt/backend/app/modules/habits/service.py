"""Habit service."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.habits.repository import HabitRepository
from app.modules.habits.schemas import (
    HabitCreate,
    HabitLogCreate,
    HabitLogResponse,
    HabitResponse,
    HabitUpdate,
)


class HabitService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = HabitRepository(db)

    async def create(self, user_id: uuid.UUID, data: HabitCreate) -> HabitResponse:
        habit = await self.repo.create(user_id, data)
        return HabitResponse.model_validate(habit)

    async def get(self, habit_id: uuid.UUID, user_id: uuid.UUID) -> HabitResponse:
        habit = await self.repo.get_by_id(habit_id, user_id)
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        return HabitResponse.model_validate(habit)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[HabitResponse]:
        items, total = await self.repo.list(
            user_id, is_active, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [HabitResponse.model_validate(h) for h in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, habit_id: uuid.UUID, user_id: uuid.UUID, data: HabitUpdate
    ) -> HabitResponse:
        habit = await self.repo.get_by_id(habit_id, user_id)
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        updated = await self.repo.update(habit, data)
        return HabitResponse.model_validate(updated)

    async def delete(self, habit_id: uuid.UUID, user_id: uuid.UUID) -> None:
        habit = await self.repo.get_by_id(habit_id, user_id)
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        await self.repo.delete(habit)

    async def log_habit(
        self, habit_id: uuid.UUID, user_id: uuid.UUID, data: HabitLogCreate
    ) -> HabitLogResponse:
        habit = await self.repo.get_by_id(habit_id, user_id)
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        log, current_streak, max_streak = await self.repo.create_or_update_log(habit, user_id, data)
        response = HabitLogResponse.model_validate(log)
        return response.model_copy(update={"current_streak": current_streak, "max_streak": max_streak})
