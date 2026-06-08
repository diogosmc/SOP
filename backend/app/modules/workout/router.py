"""Workout API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTL_DASHBOARD, build_cache_key, get_or_set_json, invalidate_user_cache
from app.core.config import get_settings
from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
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
from app.modules.workout.service import WorkoutService

router = APIRouter(prefix="/workout", tags=["workout"])


@router.get("/profile", response_model=APIResponse[ProfileResponse])
async def get_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProfileResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_profile(user_id))


@router.put("/profile", response_model=APIResponse[ProfileResponse])
async def upsert_profile(
    data: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProfileResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.upsert_profile(user_id, data))


@router.get("/exercises", response_model=APIResponse)
async def list_exercises(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_exercises(user_id, pagination))


@router.post("/exercises", response_model=APIResponse[ExerciseResponse])
async def create_exercise(
    data: ExerciseCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ExerciseResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.create_exercise(user_id, data))


@router.patch("/exercises/{exercise_id}", response_model=APIResponse[ExerciseResponse])
async def update_exercise(
    exercise_id: uuid.UUID,
    data: ExerciseUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ExerciseResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.update_exercise(exercise_id, user_id, data))


@router.delete("/exercises/{exercise_id}", response_model=APIResponse[None])
async def delete_exercise(
    exercise_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = WorkoutService(db)
    await service.delete_exercise(exercise_id, user_id)
    return APIResponse(data=None)


@router.get("/plans", response_model=APIResponse)
async def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_plans(user_id, pagination))


@router.post("/plans", response_model=APIResponse[PlanResponse])
async def create_plan(
    data: PlanCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.create_plan(user_id, data))


@router.get("/plans/{plan_id}", response_model=APIResponse[PlanDetailResponse])
async def get_plan(
    plan_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanDetailResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_plan(plan_id, user_id))


@router.patch("/plans/{plan_id}", response_model=APIResponse[PlanResponse])
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.update_plan(plan_id, user_id, data))


@router.delete("/plans/{plan_id}", response_model=APIResponse[None])
async def delete_plan(
    plan_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = WorkoutService(db)
    await service.delete_plan(plan_id, user_id)
    return APIResponse(data=None)


@router.post("/plans/{plan_id}/exercises", response_model=APIResponse[PlanExerciseResponse])
async def add_plan_exercise(
    plan_id: uuid.UUID,
    data: PlanExerciseCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanExerciseResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.add_plan_exercise(plan_id, user_id, data))


@router.delete("/plans/{plan_id}/exercises/{plan_exercise_id}", response_model=APIResponse[None])
async def delete_plan_exercise(
    plan_id: uuid.UUID,
    plan_exercise_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = WorkoutService(db)
    await service.delete_plan_exercise(plan_id, plan_exercise_id, user_id)
    return APIResponse(data=None)


@router.get("/logs", response_model=APIResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_logs(user_id, pagination))


@router.post("/logs", response_model=APIResponse[LogResponse])
async def create_log(
    data: LogCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[LogResponse]:
    service = WorkoutService(db)
    result = await service.create_log(user_id, data)
    await invalidate_user_cache(user_id, "workout:summary")
    return APIResponse(data=result)


@router.get("/logs/{log_id}", response_model=APIResponse[LogResponse])
async def get_log(
    log_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[LogResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_log(log_id, user_id))


@router.patch("/logs/{log_id}", response_model=APIResponse[LogResponse])
async def update_log(
    log_id: uuid.UUID,
    data: LogUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[LogResponse]:
    service = WorkoutService(db)
    result = await service.update_log(log_id, user_id, data)
    await invalidate_user_cache(user_id, "workout:summary")
    return APIResponse(data=result)


@router.delete("/logs/{log_id}", response_model=APIResponse[None])
async def delete_log(
    log_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = WorkoutService(db)
    await service.delete_log(log_id, user_id)
    await invalidate_user_cache(user_id, "workout:summary")
    return APIResponse(data=None)


@router.post("/logs/{log_id}/sets", response_model=APIResponse[SetLogResponse])
async def add_set_log(
    log_id: uuid.UUID,
    data: SetLogCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SetLogResponse]:
    service = WorkoutService(db)
    result = await service.add_set_log(log_id, user_id, data)
    await invalidate_user_cache(user_id, "workout:summary")
    return APIResponse(data=result)


@router.get("/summary", response_model=APIResponse[WorkoutSummary])
async def workout_summary(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WorkoutSummary]:
    service = WorkoutService(db)
    cache_key = build_cache_key("workout:summary", user_id)

    async def load() -> WorkoutSummary:
        return await service.summary(user_id)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_DASHBOARD, load)
    else:
        data = await load()
    return APIResponse(data=WorkoutSummary.model_validate(data))


@router.get("/progression", response_model=APIResponse[list[ProgressionPoint]])
async def workout_progression(
    exercise_id: Optional[uuid.UUID] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[ProgressionPoint]]:
    service = WorkoutService(db)
    return APIResponse(data=await service.progression(user_id, exercise_id))
