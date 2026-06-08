"""Reports repository — aggregated queries across modules."""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import FinanceTransaction, TransactionType
from app.modules.habits.models import Habit, HabitLog, HabitType
from app.modules.memory.models import AIMemory, DailyJournal, MemoryType
from app.modules.memory.repository import MemoryRepository
from app.modules.study.models import StudySession
from app.modules.tasks.models import Task, TaskStatus
from app.modules.workout.models import WorkoutLog


def week_bounds(ref: date) -> Tuple[date, date]:
    start = ref - timedelta(days=ref.weekday())
    return start, start + timedelta(days=6)


class ReportsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.memory_repo = MemoryRepository(db)

    async def get_journal(self, user_id: uuid.UUID, target_date: date) -> Optional[DailyJournal]:
        return await self.memory_repo.get_journal_by_date(user_id, target_date)

    async def daily_tasks(self, user_id: uuid.UUID, target_date: date) -> Tuple[int, int]:
        day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        completed = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.updated_at >= day_start,
                Task.updated_at < day_end,
            )
        )
        pending = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
        )
        return completed.scalar_one(), pending.scalar_one()

    async def habits_active_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Habit).where(Habit.user_id == user_id, Habit.active.is_(True))
        )
        return result.scalar_one()

    async def study_minutes_on_date(self, user_id: uuid.UUID, target_date: date) -> int:
        day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        result = await self.db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                StudySession.created_at >= day_start,
                StudySession.created_at < day_end,
            )
        )
        return int(result.scalar_one())

    async def workout_completed_on_date(self, user_id: uuid.UUID, target_date: date) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutLog)
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date == target_date,
                WorkoutLog.completed.is_(True),
            )
        )
        return result.scalar_one() > 0

    async def finance_on_date(self, user_id: uuid.UUID, target_date: date) -> Tuple[Decimal, Decimal]:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.INCOME, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.EXPENSE, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(FinanceTransaction)
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_date == target_date,
            )
        )
        income, expense = result.one()
        return Decimal(income), Decimal(expense)

    async def weekly_tasks_completed(self, user_id: uuid.UUID, start: date, end: date) -> int:
        start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.updated_at >= start_dt,
                Task.updated_at < end_dt,
            )
        )
        return result.scalar_one()

    async def study_minutes_in_range(self, user_id: uuid.UUID, start: date, end: date) -> int:
        start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                StudySession.created_at >= start_dt,
                StudySession.created_at < end_dt,
            )
        )
        return int(result.scalar_one())

    async def workouts_completed_in_range(self, user_id: uuid.UUID, start: date, end: date) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutLog)
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= start,
                WorkoutLog.date <= end,
                WorkoutLog.completed.is_(True),
            )
        )
        return result.scalar_one()

    async def finance_balance_in_range(self, user_id: uuid.UUID, start: date, end: date) -> Decimal:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.INCOME, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.EXPENSE, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(FinanceTransaction)
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_date >= start,
                FinanceTransaction.transaction_date <= end,
            )
        )
        income, expense = result.one()
        return Decimal(income) - Decimal(expense)

    async def habits_week_summary(self, user_id: uuid.UUID, start: date, end: date) -> str:
        active = await self.habits_active_count(user_id)
        result = await self.db.execute(
            select(func.count())
            .select_from(HabitLog)
            .join(Habit, HabitLog.habit_id == Habit.id)
            .where(
                Habit.user_id == user_id,
                HabitLog.date >= start,
                HabitLog.date <= end,
            )
        )
        logs = result.scalar_one()
        return f"{active} hábitos ativos · {logs} registros na semana"

    async def tasks_by_status(self, user_id: uuid.UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(Task.status, func.count())
            .where(Task.user_id == user_id)
            .group_by(Task.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def finance_by_category(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> List[Tuple[str, Decimal, Decimal]]:
        result = await self.db.execute(
            select(
                FinanceTransaction.category,
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.INCOME, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (FinanceTransaction.type == TransactionType.EXPENSE, FinanceTransaction.amount),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(FinanceTransaction)
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_date >= start,
                FinanceTransaction.transaction_date <= end,
            )
            .group_by(FinanceTransaction.category)
            .order_by(FinanceTransaction.category)
        )
        return [(row[0], Decimal(row[1]), Decimal(row[2])) for row in result.all()]

    async def study_minutes_by_day(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> List[Tuple[date, int]]:
        day_col = func.date(StudySession.created_at)
        result = await self.db.execute(
            select(day_col, func.coalesce(func.sum(StudySession.duration_minutes), 0))
            .where(
                StudySession.user_id == user_id,
                day_col >= start,
                day_col <= end,
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        return [(row[0], int(row[1])) for row in result.all()]

    async def workouts_by_day(self, user_id: uuid.UUID, start: date, end: date) -> List[Tuple[date, int]]:
        result = await self.db.execute(
            select(WorkoutLog.date, func.count())
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= start,
                WorkoutLog.date <= end,
                WorkoutLog.completed.is_(True),
            )
            .group_by(WorkoutLog.date)
            .order_by(WorkoutLog.date)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def habits_counts(self, user_id: uuid.UUID) -> Tuple[int, int, int]:
        active_q = await self.db.execute(
            select(func.count()).select_from(Habit).where(Habit.user_id == user_id, Habit.active.is_(True))
        )
        pos_q = await self.db.execute(
            select(func.count()).select_from(Habit).where(
                Habit.user_id == user_id, Habit.active.is_(True), Habit.type == HabitType.POSITIVE
            )
        )
        neg_q = await self.db.execute(
            select(func.count()).select_from(Habit).where(
                Habit.user_id == user_id, Habit.active.is_(True), Habit.type == HabitType.NEGATIVE
            )
        )
        return active_q.scalar_one(), pos_q.scalar_one(), neg_q.scalar_one()

    async def memories_by_type(self, user_id: uuid.UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(AIMemory.type, func.count())
            .where(AIMemory.user_id == user_id)
            .group_by(AIMemory.type)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def top_expense_category(self, user_id: uuid.UUID, start: date, end: date) -> Optional[Tuple[str, Decimal]]:
        rows = await self.finance_by_category(user_id, start, end)
        if not rows:
            return None
        top = max(rows, key=lambda r: r[2])
        if top[2] <= 0:
            return None
        return top[0], top[2]

    async def days_since_last_workout(self, user_id: uuid.UUID, ref: date) -> Optional[int]:
        result = await self.db.execute(
            select(func.max(WorkoutLog.date)).where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.completed.is_(True),
            )
        )
        last = result.scalar_one()
        if not last:
            return None
        return (ref - last).days

    async def pending_tasks_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
        )
        return result.scalar_one()
