"""Reports repository."""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import FinanceTransaction, TransactionType
from app.modules.habits.models import Habit, HabitLog
from app.modules.memory.models import DailyJournal, WeeklyReview
from app.modules.study.models import Flashcard, StudySession, StudyTopic, TopicStatus
from app.modules.tasks.models import Task, TaskStatus
from app.modules.workout.models import WorkoutSession, WorkoutSet


class ReportsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_daily_journal(
        self, user_id: uuid.UUID, target_date: date
    ) -> Optional[DailyJournal]:
        day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        result = await self.db.execute(
            select(DailyJournal).where(
                DailyJournal.user_id == user_id,
                DailyJournal.date >= day_start,
                DailyJournal.date < day_end,
            )
        )
        return result.scalar_one_or_none()

    async def list_daily_journals(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> List[DailyJournal]:
        range_start = datetime.combine(start_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await self.db.execute(
            select(DailyJournal)
            .where(
                DailyJournal.user_id == user_id,
                DailyJournal.date >= range_start,
                DailyJournal.date < range_end,
            )
            .order_by(DailyJournal.date.desc())
        )
        return list(result.scalars().all())

    async def get_weekly_review(
        self, user_id: uuid.UUID, week_reference: str
    ) -> Optional[WeeklyReview]:
        result = await self.db.execute(
            select(WeeklyReview).where(
                WeeklyReview.user_id == user_id,
                WeeklyReview.week_reference == week_reference,
            )
        )
        return result.scalar_one_or_none()

    async def list_weekly_reviews(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[WeeklyReview]:
        result = await self.db.execute(
            select(WeeklyReview)
            .where(WeeklyReview.user_id == user_id)
            .order_by(WeeklyReview.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert_weekly_review(
        self,
        user_id: uuid.UUID,
        week_reference: str,
        summary: Optional[str] = None,
        wins: Optional[str] = None,
        failures: Optional[str] = None,
        patterns: Optional[str] = None,
        recommendations: Optional[str] = None,
    ) -> WeeklyReview:
        review = await self.get_weekly_review(user_id, week_reference)
        if review:
            review.summary = summary
            review.wins = wins
            review.failures = failures
            review.patterns = patterns
            review.recommendations = recommendations
        else:
            review = WeeklyReview(
                user_id=user_id,
                week_reference=week_reference,
                summary=summary,
                wins=wins,
                failures=failures,
                patterns=patterns,
                recommendations=recommendations,
            )
            self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_finance_analytics(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> Tuple[float, float, int]:
        income_result = await self.db.execute(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_type == TransactionType.INCOME,
                FinanceTransaction.transaction_date >= start_date,
                FinanceTransaction.transaction_date <= end_date,
            )
        )
        expense_result = await self.db.execute(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_type == TransactionType.EXPENSE,
                FinanceTransaction.transaction_date >= start_date,
                FinanceTransaction.transaction_date <= end_date,
            )
        )
        count_result = await self.db.execute(
            select(func.count())
            .select_from(FinanceTransaction)
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_date >= start_date,
                FinanceTransaction.transaction_date <= end_date,
            )
        )
        return (
            float(income_result.scalar_one()),
            float(expense_result.scalar_one()),
            int(count_result.scalar_one()),
        )

    async def get_study_analytics(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> Tuple[int, int, int, int]:
        range_start = datetime.combine(start_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        range_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        minutes_result = await self.db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                StudySession.created_at >= range_start,
                StudySession.created_at < range_end,
            )
        )
        sessions_result = await self.db.execute(
            select(func.count())
            .select_from(StudySession)
            .where(
                StudySession.user_id == user_id,
                StudySession.created_at >= range_start,
                StudySession.created_at < range_end,
            )
        )
        mastered_result = await self.db.execute(
            select(func.count())
            .select_from(StudyTopic)
            .where(StudyTopic.user_id == user_id, StudyTopic.status == TopicStatus.MASTERED)
        )
        flashcards_result = await self.db.execute(
            select(func.count()).select_from(Flashcard).where(Flashcard.user_id == user_id)
        )
        return (
            int(minutes_result.scalar_one()),
            int(sessions_result.scalar_one()),
            int(mastered_result.scalar_one()),
            int(flashcards_result.scalar_one()),
        )

    async def get_workout_analytics(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> Tuple[int, int, float]:
        sessions_result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutSession)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.session_date >= start_date,
                WorkoutSession.session_date <= end_date,
            )
        )
        sets_result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutSet)
            .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
            .where(
                WorkoutSet.user_id == user_id,
                WorkoutSession.session_date >= start_date,
                WorkoutSession.session_date <= end_date,
            )
        )
        volume_result = await self.db.execute(
            select(func.coalesce(func.sum(WorkoutSet.reps * WorkoutSet.weight_kg), 0))
            .select_from(WorkoutSet)
            .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
            .where(
                WorkoutSet.user_id == user_id,
                WorkoutSession.session_date >= start_date,
                WorkoutSession.session_date <= end_date,
            )
        )
        return (
            int(sessions_result.scalar_one()),
            int(sets_result.scalar_one()),
            float(volume_result.scalar_one()),
        )

    async def get_tasks_analytics(self, user_id: uuid.UUID) -> Tuple[int, int]:
        completed_result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
        )
        pending_result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
        )
        return int(completed_result.scalar_one()), int(pending_result.scalar_one())

    async def get_habits_analytics(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> Tuple[int, int]:
        active_result = await self.db.execute(
            select(func.count()).select_from(Habit).where(Habit.user_id == user_id, Habit.is_active)
        )
        completions_result = await self.db.execute(
            select(func.count())
            .select_from(HabitLog)
            .join(Habit, HabitLog.habit_id == Habit.id)
            .where(
                Habit.user_id == user_id,
                HabitLog.log_date >= start_date,
                HabitLog.log_date <= end_date,
                HabitLog.completed.is_(True),
            )
        )
        return int(active_result.scalar_one()), int(completions_result.scalar_one())
