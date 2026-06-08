"""Workout service."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.workout.repository import WorkoutRepository
from app.modules.workout.schemas import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseUpdate,
    MuscleVolume,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    ProfileResponse,
    ProfileUpdate,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    WeeklyVolumeSummary,
    WorkoutSetCreate,
    WorkoutSetResponse,
)


class WorkoutService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = WorkoutRepository(db)

    def _session_response(self, session, sets: List) -> SessionResponse:
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            plan_id=session.plan_id,
            session_date=session.session_date,
            notes=session.notes,
            duration_minutes=session.duration_minutes,
            sets=[WorkoutSetResponse.model_validate(s) for s in sets],
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def create_plan(self, user_id: uuid.UUID, data: PlanCreate) -> PlanResponse:
        plan = await self.repo.create_plan(user_id, data)
        return PlanResponse.model_validate(plan)

    async def get_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> PlanResponse:
        plan = await self.repo.get_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return PlanResponse.model_validate(plan)

    async def list_plans(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[PlanResponse]:
        items, total = await self.repo.list_plans(
            user_id, is_active, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [PlanResponse.model_validate(p) for p in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_plan(
        self, plan_id: uuid.UUID, user_id: uuid.UUID, data: PlanUpdate
    ) -> PlanResponse:
        plan = await self.repo.get_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        updated = await self.repo.update_plan(plan, data)
        return PlanResponse.model_validate(updated)

    async def delete_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> None:
        plan = await self.repo.get_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        await self.repo.delete_plan(plan)

    async def create_exercise(self, user_id: uuid.UUID, data: ExerciseCreate) -> ExerciseResponse:
        plan = await self.repo.get_plan(data.plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        exercise = await self.repo.create_exercise(user_id, data)
        return ExerciseResponse.model_validate(exercise)

    async def get_exercise(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> ExerciseResponse:
        exercise = await self.repo.get_exercise(exercise_id, user_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        return ExerciseResponse.model_validate(exercise)

    async def list_exercises(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        plan_id: Optional[uuid.UUID] = None,
    ) -> PaginatedResponse[ExerciseResponse]:
        items, total = await self.repo.list_exercises(
            user_id, plan_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [ExerciseResponse.model_validate(e) for e in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_exercise(
        self, exercise_id: uuid.UUID, user_id: uuid.UUID, data: ExerciseUpdate
    ) -> ExerciseResponse:
        exercise = await self.repo.get_exercise(exercise_id, user_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        updated = await self.repo.update_exercise(exercise, data)
        return ExerciseResponse.model_validate(updated)

    async def delete_exercise(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> None:
        exercise = await self.repo.get_exercise(exercise_id, user_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        await self.repo.delete_exercise(exercise)

    async def create_session(self, user_id: uuid.UUID, data: SessionCreate) -> SessionResponse:
        if data.plan_id:
            plan = await self.repo.get_plan(data.plan_id, user_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        for set_data in data.sets:
            exercise = await self.repo.get_exercise(set_data.exercise_id, user_id)
            if not exercise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exercise {set_data.exercise_id} not found",
                )
        session = await self.repo.create_session(user_id, data)
        sets = await self.repo.get_sets_for_session(session.id, user_id)
        return self._session_response(session, sets)

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionResponse:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        sets = await self.repo.get_sets_for_session(session_id, user_id)
        return self._session_response(session, sets)

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        plan_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PaginatedResponse[SessionResponse]:
        items, total = await self.repo.list_sessions(
            user_id, plan_id, start_date, end_date, pagination.offset, pagination.page_size
        )
        responses = []
        for session in items:
            sets = await self.repo.get_sets_for_session(session.id, user_id)
            responses.append(self._session_response(session, sets))
        return PaginatedResponse.create(responses, total, pagination.page, pagination.page_size)

    async def update_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID, data: SessionUpdate
    ) -> SessionResponse:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if data.plan_id:
            plan = await self.repo.get_plan(data.plan_id, user_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        updated = await self.repo.update_session(session, data)
        sets = await self.repo.get_sets_for_session(session_id, user_id)
        return self._session_response(updated, sets)

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        await self.repo.delete_session(session)

    async def add_set(
        self, session_id: uuid.UUID, user_id: uuid.UUID, data: WorkoutSetCreate
    ) -> WorkoutSetResponse:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        exercise = await self.repo.get_exercise(data.exercise_id, user_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        workout_set = await self.repo.add_set(session_id, user_id, data)
        return WorkoutSetResponse.model_validate(workout_set)

    async def get_profile(self, user_id: uuid.UUID) -> ProfileResponse:
        profile = await self.repo.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return ProfileResponse.model_validate(profile)

    async def update_profile(self, user_id: uuid.UUID, data: ProfileUpdate) -> ProfileResponse:
        profile = await self.repo.upsert_profile(user_id, data)
        return ProfileResponse.model_validate(profile)

    async def get_weekly_volume(
        self, user_id: uuid.UUID, reference_date: Optional[date] = None
    ) -> WeeklyVolumeSummary:
        ref = reference_date or date.today()
        week_start = ref - timedelta(days=ref.weekday())
        week_end = week_start + timedelta(days=6)

        total_sessions, rows = await self.repo.get_weekly_volume(user_id, week_start, week_end)

        by_muscle: List[MuscleVolume] = []
        total_sets = 0
        total_reps = 0
        total_volume = Decimal("0")

        for muscle_group, sets_count, reps_sum, volume_sum in rows:
            total_sets += sets_count
            total_reps += reps_sum
            total_volume += volume_sum
            by_muscle.append(
                MuscleVolume(
                    muscle_group=muscle_group,
                    total_sets=sets_count,
                    total_reps=reps_sum,
                    total_volume_kg=volume_sum,
                )
            )

        return WeeklyVolumeSummary(
            week_start=week_start,
            week_end=week_end,
            total_sessions=total_sessions,
            total_sets=total_sets,
            total_reps=total_reps,
            total_volume_kg=total_volume,
            by_muscle_group=by_muscle,
        )
