"""Workout service."""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.workout.repository import WorkoutRepository
from app.modules.workout.schemas import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseUpdate,
    LogCreate,
    LogResponse,
    LogUpdate,
    PlanCreate,
    PlanDetailResponse,
    PlanExerciseCreate,
    PlanExerciseResponse,
    PlanResponse,
    PlanUpdate,
    ProfileResponse,
    ProfileUpdate,
    ProgressionPoint,
    SetLogCreate,
    SetLogResponse,
    WorkoutSummary,
)


class WorkoutService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = WorkoutRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> ProfileResponse:
        profile = await self.repo.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return ProfileResponse.model_validate(profile)

    async def upsert_profile(self, user_id: uuid.UUID, data: ProfileUpdate) -> ProfileResponse:
        profile = await self.repo.upsert_profile(user_id, data)
        return ProfileResponse.model_validate(profile)

    async def create_exercise(self, user_id: uuid.UUID, data: ExerciseCreate) -> ExerciseResponse:
        exercise = await self.repo.create_exercise(user_id, data)
        return ExerciseResponse.model_validate(exercise)

    async def list_exercises(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[ExerciseResponse]:
        items, total = await self.repo.list_exercises(user_id, pagination.offset, pagination.page_size)
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
        if not exercise or exercise.user_id is None:
            if exercise and exercise.user_id is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit global exercise")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        updated = await self.repo.update_exercise(exercise, data)
        return ExerciseResponse.model_validate(updated)

    async def delete_exercise(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> None:
        exercise = await self.repo.get_exercise(exercise_id, user_id)
        if not exercise or exercise.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        await self.repo.delete_exercise(exercise)

    async def create_plan(self, user_id: uuid.UUID, data: PlanCreate) -> PlanResponse:
        plan = await self.repo.create_plan(user_id, data)
        return PlanResponse.model_validate(plan)

    async def get_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> PlanDetailResponse:
        plan = await self.repo.get_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        exercises = [
            PlanExerciseResponse(
                id=item.id,
                plan_id=item.plan_id,
                exercise_id=item.exercise_id,
                exercise_name=item.exercise.name if item.exercise else None,
                day_label=item.day_label,
                sets=item.sets,
                reps=item.reps,
                target_load_kg=item.target_load_kg,
                rest_seconds=item.rest_seconds,
                order_index=item.order_index,
                notes=item.notes,
            )
            for item in sorted(plan.plan_exercises, key=lambda x: (x.day_label or "", x.order_index))
        ]
        base = PlanResponse.model_validate(plan)
        return PlanDetailResponse(**base.model_dump(), exercises=exercises)

    async def list_plans(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[PlanResponse]:
        items, total = await self.repo.list_plans(user_id, pagination.offset, pagination.page_size)
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

    async def add_plan_exercise(
        self, plan_id: uuid.UUID, user_id: uuid.UUID, data: PlanExerciseCreate
    ) -> PlanExerciseResponse:
        plan = await self.repo.get_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        item = await self.repo.add_plan_exercise(plan, user_id, data)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        await self.repo.db.refresh(item, attribute_names=["exercise"])
        return PlanExerciseResponse(
            id=item.id,
            plan_id=item.plan_id,
            exercise_id=item.exercise_id,
            exercise_name=item.exercise.name if item.exercise else None,
            day_label=item.day_label,
            sets=item.sets,
            reps=item.reps,
            target_load_kg=item.target_load_kg,
            rest_seconds=item.rest_seconds,
            order_index=item.order_index,
            notes=item.notes,
        )

    async def delete_plan_exercise(
        self, plan_id: uuid.UUID, plan_exercise_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        item = await self.repo.get_plan_exercise(plan_exercise_id, plan_id, user_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan exercise not found")
        await self.repo.delete_plan_exercise(item)

    async def create_log(self, user_id: uuid.UUID, data: LogCreate) -> LogResponse:
        log = await self.repo.create_log(user_id, data)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        loaded = await self.repo.get_log(log.id, user_id)
        return self._log_response(loaded or log, empty_sets=loaded is None)

    async def get_log(self, log_id: uuid.UUID, user_id: uuid.UUID) -> LogResponse:
        log = await self.repo.get_log(log_id, user_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
        return self._log_response(log)

    async def list_logs(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[LogResponse]:
        items, total = await self.repo.list_logs(user_id, pagination.offset, pagination.page_size)
        return PaginatedResponse.create(
            [self._log_response(log) for log in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_log(
        self, log_id: uuid.UUID, user_id: uuid.UUID, data: LogUpdate
    ) -> LogResponse:
        log = await self.repo.get_log(log_id, user_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
        updated = await self.repo.update_log(log, data)
        loaded = await self.repo.get_log(updated.id, user_id)
        return self._log_response(loaded or updated, empty_sets=loaded is None)

    async def delete_log(self, log_id: uuid.UUID, user_id: uuid.UUID) -> None:
        log = await self.repo.get_log(log_id, user_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
        await self.repo.delete_log(log)

    async def add_set_log(
        self, log_id: uuid.UUID, user_id: uuid.UUID, data: SetLogCreate
    ) -> SetLogResponse:
        log = await self.repo.get_log(log_id, user_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
        set_log = await self.repo.add_set_log(log, user_id, data)
        if not set_log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        await self.repo.db.refresh(set_log, attribute_names=["exercise"])
        return SetLogResponse(
            id=set_log.id,
            workout_log_id=set_log.workout_log_id,
            exercise_id=set_log.exercise_id,
            exercise_name=set_log.exercise.name if set_log.exercise else None,
            set_number=set_log.set_number,
            reps=set_log.reps,
            load_kg=set_log.load_kg,
            notes=set_log.notes,
            created_at=set_log.created_at,
        )

    async def summary(self, user_id: uuid.UUID) -> WorkoutSummary:
        return WorkoutSummary(**await self.repo.summary(user_id))

    async def progression(
        self, user_id: uuid.UUID, exercise_id: Optional[uuid.UUID] = None
    ) -> List[ProgressionPoint]:
        rows = await self.repo.progression(user_id, exercise_id)
        return [ProgressionPoint(**row) for row in rows]

    @staticmethod
    def _log_response(log, *, empty_sets: bool = False) -> LogResponse:
        raw_sets = [] if empty_sets else getattr(log, "set_logs", None) or []
        sets = [
            SetLogResponse(
                id=s.id,
                workout_log_id=s.workout_log_id,
                exercise_id=s.exercise_id,
                exercise_name=s.exercise.name if getattr(s, "exercise", None) else None,
                set_number=s.set_number,
                reps=s.reps,
                load_kg=s.load_kg,
                notes=s.notes,
                created_at=s.created_at,
            )
            for s in raw_sets
        ]
        base = LogResponse.model_validate(log)
        return LogResponse(**base.model_dump(exclude={"sets"}), sets=sets)
