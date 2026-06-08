"""Workout repository."""

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.workout.models import Exercise, PhysicalProfile, WorkoutPlan, WorkoutSession, WorkoutSet
from app.modules.workout.schemas import (
    ExerciseCreate,
    ExerciseUpdate,
    PlanCreate,
    PlanUpdate,
    ProfileUpdate,
    SessionCreate,
    SessionUpdate,
    WorkoutSetCreate,
)


class WorkoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Plans ---

    async def create_plan(self, user_id: uuid.UUID, data: PlanCreate) -> WorkoutPlan:
        plan = WorkoutPlan(user_id=user_id, **data.model_dump())
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def get_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> Optional[WorkoutPlan]:
        result = await self.db.execute(
            select(WorkoutPlan).where(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        user_id: uuid.UUID,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[WorkoutPlan], int]:
        filters = [WorkoutPlan.user_id == user_id]
        if is_active is not None:
            filters.append(WorkoutPlan.is_active == is_active)

        query = (
            select(WorkoutPlan)
            .where(*filters)
            .order_by(WorkoutPlan.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(WorkoutPlan).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_plan(self, plan: WorkoutPlan, data: PlanUpdate) -> WorkoutPlan:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan: WorkoutPlan) -> None:
        await self.db.delete(plan)
        await self.db.flush()

    # --- Exercises ---

    async def create_exercise(self, user_id: uuid.UUID, data: ExerciseCreate) -> Exercise:
        exercise = Exercise(user_id=user_id, **data.model_dump())
        self.db.add(exercise)
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def get_exercise(
        self, exercise_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Exercise]:
        result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_exercises(
        self,
        user_id: uuid.UUID,
        plan_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Exercise], int]:
        filters = [Exercise.user_id == user_id]
        if plan_id:
            filters.append(Exercise.plan_id == plan_id)

        query = (
            select(Exercise)
            .where(*filters)
            .order_by(Exercise.name)
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(Exercise).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_exercise(self, exercise: Exercise, data: ExerciseUpdate) -> Exercise:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(exercise, field, value)
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def delete_exercise(self, exercise: Exercise) -> None:
        await self.db.delete(exercise)
        await self.db.flush()

    # --- Sessions ---

    async def create_session(self, user_id: uuid.UUID, data: SessionCreate) -> WorkoutSession:
        session_data = data.model_dump(exclude={"sets"})
        session = WorkoutSession(user_id=user_id, **session_data)
        self.db.add(session)
        await self.db.flush()

        for set_data in data.sets:
            workout_set = WorkoutSet(
                session_id=session.id,
                user_id=user_id,
                **set_data.model_dump(),
            )
            self.db.add(workout_set)

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[WorkoutSession]:
        result = await self.db.execute(
            select(WorkoutSession).where(
                WorkoutSession.id == session_id, WorkoutSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        plan_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[WorkoutSession], int]:
        filters = [WorkoutSession.user_id == user_id]
        if plan_id:
            filters.append(WorkoutSession.plan_id == plan_id)
        if start_date:
            filters.append(WorkoutSession.session_date >= start_date)
        if end_date:
            filters.append(WorkoutSession.session_date <= end_date)

        query = (
            select(WorkoutSession)
            .where(*filters)
            .order_by(WorkoutSession.session_date.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(WorkoutSession).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_session(self, session: WorkoutSession, data: SessionUpdate) -> WorkoutSession:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(session, field, value)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def delete_session(self, session: WorkoutSession) -> None:
        await self.db.delete(session)
        await self.db.flush()

    async def add_set(
        self, session_id: uuid.UUID, user_id: uuid.UUID, data: WorkoutSetCreate
    ) -> WorkoutSet:
        workout_set = WorkoutSet(session_id=session_id, user_id=user_id, **data.model_dump())
        self.db.add(workout_set)
        await self.db.flush()
        await self.db.refresh(workout_set)
        return workout_set

    async def get_sets_for_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[WorkoutSet]:
        result = await self.db.execute(
            select(WorkoutSet)
            .where(WorkoutSet.session_id == session_id, WorkoutSet.user_id == user_id)
            .order_by(WorkoutSet.set_number)
        )
        return list(result.scalars().all())

    # --- Profile ---

    async def get_profile(self, user_id: uuid.UUID) -> Optional[PhysicalProfile]:
        result = await self.db.execute(
            select(PhysicalProfile).where(PhysicalProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_profile(self, user_id: uuid.UUID, data: ProfileUpdate) -> PhysicalProfile:
        profile = await self.get_profile(user_id)
        if profile:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(profile, field, value)
        else:
            profile = PhysicalProfile(user_id=user_id, **data.model_dump(exclude_unset=True))
            self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    # --- Weekly volume ---

    async def get_weekly_volume(
        self, user_id: uuid.UUID, week_start: date, week_end: date
    ) -> Tuple[int, List[Tuple[str, int, int, Decimal]]]:
        sessions_result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutSession)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.session_date >= week_start,
                WorkoutSession.session_date <= week_end,
            )
        )
        total_sessions = sessions_result.scalar_one()

        volume_result = await self.db.execute(
            select(
                Exercise.muscle_group,
                func.count(WorkoutSet.id),
                func.coalesce(func.sum(WorkoutSet.reps), 0),
                func.coalesce(func.sum(WorkoutSet.reps * WorkoutSet.weight_kg), 0),
            )
            .join(Exercise, WorkoutSet.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
            .where(
                WorkoutSet.user_id == user_id,
                WorkoutSession.session_date >= week_start,
                WorkoutSession.session_date <= week_end,
            )
            .group_by(Exercise.muscle_group)
        )
        rows = []
        for muscle_group, sets_count, reps_sum, volume_sum in volume_result.all():
            group = muscle_group or "other"
            rows.append((group, int(sets_count), int(reps_sum), Decimal(str(volume_sum))))
        return total_sessions, rows
