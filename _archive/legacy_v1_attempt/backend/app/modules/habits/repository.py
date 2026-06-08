"""Habit repository."""

import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.habits.models import Habit, HabitLog
from app.modules.habits.schemas import HabitCreate, HabitLogCreate, HabitUpdate


def _calculate_streaks(completed_dates: List[date]) -> Tuple[int, int]:
    if not completed_dates:
        return 0, 0

    sorted_dates = sorted(set(completed_dates))
    today = date.today()

    max_streak = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            run += 1
            max_streak = max(max_streak, run)
        else:
            run = 1

    most_recent = sorted_dates[-1]
    if most_recent < today - timedelta(days=1):
        current_streak = 0
    else:
        current_streak = 1
        for i in range(len(sorted_dates) - 1, 0, -1):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                current_streak += 1
            else:
                break

    return current_streak, max(max_streak, current_streak)


class HabitRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: HabitCreate) -> Habit:
        habit = Habit(user_id=user_id, **data.model_dump())
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
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Habit], int]:
        query = select(Habit).where(Habit.user_id == user_id)
        count_query = select(func.count()).select_from(Habit).where(Habit.user_id == user_id)
        if is_active is not None:
            query = query.where(Habit.is_active == is_active)
            count_query = count_query.where(Habit.is_active == is_active)
        query = query.order_by(Habit.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, habit: Habit, data: HabitUpdate) -> Habit:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(habit, field, value)
        await self.db.flush()
        await self.db.refresh(habit)
        return habit

    async def delete(self, habit: Habit) -> None:
        await self.db.delete(habit)
        await self.db.flush()

    async def get_log_by_date(
        self, habit_id: uuid.UUID, log_date: date
    ) -> Optional[HabitLog]:
        result = await self.db.execute(
            select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.log_date == log_date)
        )
        return result.scalar_one_or_none()

    async def create_or_update_log(
        self, habit: Habit, user_id: uuid.UUID, data: HabitLogCreate
    ) -> Tuple[HabitLog, int, int]:
        existing = await self.get_log_by_date(habit.id, data.log_date)
        if existing:
            existing.completed = data.completed
            existing.notes = data.notes
            log = existing
        else:
            log = HabitLog(
                habit_id=habit.id,
                user_id=user_id,
                log_date=data.log_date,
                completed=data.completed,
                notes=data.notes,
            )
            self.db.add(log)

        await self.db.flush()
        current_streak, max_streak = await self._update_habit_streaks(habit)
        await self.db.refresh(log)
        return log, current_streak, max_streak

    async def _update_habit_streaks(self, habit: Habit) -> Tuple[int, int]:
        result = await self.db.execute(
            select(HabitLog.log_date).where(
                HabitLog.habit_id == habit.id, HabitLog.completed.is_(True)
            )
        )
        completed_dates = list(result.scalars().all())
        current_streak, max_streak = _calculate_streaks(completed_dates)
        habit.current_streak = current_streak
        habit.max_streak = max(habit.max_streak, max_streak)
        await self.db.flush()
        await self.db.refresh(habit)
        return current_streak, habit.max_streak
