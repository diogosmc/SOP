"""Workout repository."""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.workout.models import (
    Exercise,
    ExerciseSetLog,
    WorkoutLog,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutProfile,
)
from app.modules.workout.schemas import (
    ExerciseCreate,
    ExerciseUpdate,
    LogCreate,
    LogUpdate,
    PlanCreate,
    PlanExerciseCreate,
    PlanUpdate,
    ProfileUpdate,
    SetLogCreate,
)


def _week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def _month_start(today: date) -> date:
    return today.replace(day=1)


class WorkoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> Optional[WorkoutProfile]:
        result = await self.db.execute(
            select(WorkoutProfile).where(WorkoutProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_profile(self, user_id: uuid.UUID, data: ProfileUpdate) -> WorkoutProfile:
        profile = await self.get_profile(user_id)
        if profile is None:
            profile = WorkoutProfile(user_id=user_id, **data.model_dump())
            self.db.add(profile)
        else:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(profile, field, value)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def create_exercise(self, user_id: uuid.UUID, data: ExerciseCreate) -> Exercise:
        exercise = Exercise(user_id=user_id, **data.model_dump())
        self.db.add(exercise)
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def get_exercise(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Exercise]:
        result = await self.db.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                or_(Exercise.user_id == user_id, Exercise.user_id.is_(None)),
            )
        )
        return result.scalar_one_or_none()

    async def list_exercises(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 100
    ) -> Tuple[List[Exercise], int]:
        query = select(Exercise).where(
            or_(Exercise.user_id == user_id, Exercise.user_id.is_(None))
        )
        count_query = select(func.count()).select_from(Exercise).where(
            or_(Exercise.user_id == user_id, Exercise.user_id.is_(None))
        )
        query = query.order_by(Exercise.name).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def update_exercise(self, exercise: Exercise, data: ExerciseUpdate) -> Exercise:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(exercise, field, value)
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def delete_exercise(self, exercise: Exercise) -> None:
        await self.db.delete(exercise)
        await self.db.flush()

    async def create_plan(self, user_id: uuid.UUID, data: PlanCreate) -> WorkoutPlan:
        if data.active:
            await self._deactivate_plans(user_id)
        plan = WorkoutPlan(user_id=user_id, **data.model_dump())
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def _deactivate_plans(self, user_id: uuid.UUID, except_id: Optional[uuid.UUID] = None) -> None:
        query = select(WorkoutPlan).where(WorkoutPlan.user_id == user_id, WorkoutPlan.active.is_(True))
        if except_id:
            query = query.where(WorkoutPlan.id != except_id)
        result = await self.db.execute(query)
        for plan in result.scalars().all():
            plan.active = False
        await self.db.flush()

    async def get_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> Optional[WorkoutPlan]:
        result = await self.db.execute(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.plan_exercises).selectinload(WorkoutPlanExercise.exercise))
            .where(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_plans(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> Tuple[List[WorkoutPlan], int]:
        query = select(WorkoutPlan).where(WorkoutPlan.user_id == user_id).order_by(WorkoutPlan.name)
        count_query = select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
        result = await self.db.execute(query.offset(offset).limit(limit))
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def update_plan(self, plan: WorkoutPlan, data: PlanUpdate) -> WorkoutPlan:
        payload = data.model_dump(exclude_unset=True)
        if payload.get("active") is True:
            await self._deactivate_plans(plan.user_id, except_id=plan.id)
        for field, value in payload.items():
            setattr(plan, field, value)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan: WorkoutPlan) -> None:
        await self.db.delete(plan)
        await self.db.flush()

    async def add_plan_exercise(
        self, plan: WorkoutPlan, user_id: uuid.UUID, data: PlanExerciseCreate
    ) -> Optional[WorkoutPlanExercise]:
        exercise = await self.get_exercise(data.exercise_id, user_id)
        if not exercise:
            return None
        item = WorkoutPlanExercise(plan_id=plan.id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_plan_exercise(
        self, plan_exercise_id: uuid.UUID, plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[WorkoutPlanExercise]:
        result = await self.db.execute(
            select(WorkoutPlanExercise)
            .join(WorkoutPlan, WorkoutPlanExercise.plan_id == WorkoutPlan.id)
            .where(
                WorkoutPlanExercise.id == plan_exercise_id,
                WorkoutPlanExercise.plan_id == plan_id,
                WorkoutPlan.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_plan_exercise(self, item: WorkoutPlanExercise) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def create_log(self, user_id: uuid.UUID, data: LogCreate) -> Optional[WorkoutLog]:
        if data.plan_id:
            plan = await self.get_plan(data.plan_id, user_id)
            if not plan:
                return None
        log = WorkoutLog(user_id=user_id, **data.model_dump())
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def get_log(self, log_id: uuid.UUID, user_id: uuid.UUID) -> Optional[WorkoutLog]:
        result = await self.db.execute(
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.set_logs).selectinload(ExerciseSetLog.exercise))
            .where(WorkoutLog.id == log_id, WorkoutLog.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_logs(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> Tuple[List[WorkoutLog], int]:
        query = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.set_logs).selectinload(ExerciseSetLog.exercise))
            .where(WorkoutLog.user_id == user_id)
            .order_by(WorkoutLog.date.desc(), WorkoutLog.created_at.desc())
        )
        count_query = select(func.count()).select_from(WorkoutLog).where(WorkoutLog.user_id == user_id)
        result = await self.db.execute(query.offset(offset).limit(limit))
        count = await self.db.execute(count_query)
        return list(result.scalars().all()), count.scalar_one()

    async def update_log(self, log: WorkoutLog, data: LogUpdate) -> WorkoutLog:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(log, field, value)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def delete_log(self, log: WorkoutLog) -> None:
        await self.db.delete(log)
        await self.db.flush()

    async def add_set_log(
        self, log: WorkoutLog, user_id: uuid.UUID, data: SetLogCreate
    ) -> Optional[ExerciseSetLog]:
        exercise = await self.get_exercise(data.exercise_id, user_id)
        if not exercise:
            return None
        set_log = ExerciseSetLog(workout_log_id=log.id, **data.model_dump())
        self.db.add(set_log)
        await self.db.flush()
        await self.db.refresh(set_log)
        return set_log

    async def summary(self, user_id: uuid.UUID) -> dict:
        today = date.today()
        week_start = _week_start(today)
        month_start = _month_start(today)

        week_count = await self.db.execute(
            select(func.count())
            .select_from(WorkoutLog)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.date >= week_start)
        )
        month_count = await self.db.execute(
            select(func.count())
            .select_from(WorkoutLog)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.date >= month_start)
        )
        last_date = await self.db.execute(
            select(func.max(WorkoutLog.date)).where(WorkoutLog.user_id == user_id)
        )
        active_plan = await self.db.execute(
            select(WorkoutPlan.name)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.active.is_(True))
            .limit(1)
        )
        completed = await self.db.execute(
            select(func.count())
            .select_from(WorkoutLog)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.completed.is_(True))
        )
        total_logs = await self.db.execute(
            select(func.count()).select_from(WorkoutLog).where(WorkoutLog.user_id == user_id)
        )
        volume = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(ExerciseSetLog.reps * func.coalesce(ExerciseSetLog.load_kg, 0)),
                    0,
                )
            )
            .select_from(ExerciseSetLog)
            .join(WorkoutLog, ExerciseSetLog.workout_log_id == WorkoutLog.id)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.date >= week_start)
        )

        total = total_logs.scalar_one()
        done = completed.scalar_one()
        rate = (done / total * 100) if total else 0.0

        return {
            "workouts_this_week": week_count.scalar_one(),
            "workouts_this_month": month_count.scalar_one(),
            "total_volume_week": Decimal(volume.scalar_one()),
            "last_workout_date": last_date.scalar_one(),
            "active_plan": active_plan.scalar_one_or_none(),
            "completed_rate": round(rate, 1),
        }

    async def progression(
        self, user_id: uuid.UUID, exercise_id: Optional[uuid.UUID] = None
    ) -> List[dict]:
        query = (
            select(
                WorkoutLog.date,
                ExerciseSetLog.exercise_id,
                Exercise.name,
                ExerciseSetLog.load_kg,
                ExerciseSetLog.reps,
                ExerciseSetLog.set_number,
            )
            .join(WorkoutLog, ExerciseSetLog.workout_log_id == WorkoutLog.id)
            .join(Exercise, ExerciseSetLog.exercise_id == Exercise.id)
            .where(WorkoutLog.user_id == user_id)
            .order_by(WorkoutLog.date, ExerciseSetLog.set_number)
        )
        if exercise_id:
            query = query.where(ExerciseSetLog.exercise_id == exercise_id)
        result = await self.db.execute(query)
        return [
            {
                "date": row[0],
                "exercise_id": row[1],
                "exercise_name": row[2],
                "load_kg": row[3],
                "reps": row[4],
                "set_number": row[5],
            }
            for row in result.all()
        ]
