"""Habit repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.habits.models import Habit, HabitType
from app.modules.habits.schemas import HabitCreate, HabitUpdate


class HabitRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: HabitCreate) -> Habit:
        habit = Habit(user_id=user_id, **data.model_dump(mode="json"))
        self.db.add(habit)
        await self.db.flush()
        await self.db.refresh(habit)
        return habit

    async def get_by_id(self, habit_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Habit]:
        result = await self.db.execute(
            select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        active: Optional[bool] = None,
        habit_type: Optional[HabitType] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Habit], int]:
        query = select(Habit).where(Habit.user_id == user_id)
        count_query = select(func.count()).select_from(Habit).where(Habit.user_id == user_id)
        if active is not None:
            query = query.where(Habit.active == active)
            count_query = count_query.where(Habit.active == active)
        if habit_type is not None:
            query = query.where(Habit.type == habit_type)
            count_query = count_query.where(Habit.type == habit_type)
        query = query.order_by(Habit.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, habit: Habit, data: HabitUpdate) -> Habit:
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(habit, field, value)
        await self.db.flush()
        await self.db.refresh(habit)
        return habit

    async def delete(self, habit: Habit) -> None:
        await self.db.delete(habit)
        await self.db.flush()
