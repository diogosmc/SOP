"""Workout API routes."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.workout.schemas import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseUpdate,
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
from app.modules.workout.service import WorkoutService

router = APIRouter(prefix="/workout", tags=["workout"])


@router.post("/plans", response_model=APIResponse[PlanResponse])
async def create_plan(
    data: PlanCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.create_plan(user_id, data))


@router.get("/plans", response_model=APIResponse)
async def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_plans(user_id, pagination, is_active))


@router.get("/plans/{plan_id}", response_model=APIResponse[PlanResponse])
async def get_plan(
    plan_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlanResponse]:
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


@router.post("/exercises", response_model=APIResponse[ExerciseResponse])
async def create_exercise(
    data: ExerciseCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ExerciseResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.create_exercise(user_id, data))


@router.get("/exercises", response_model=APIResponse)
async def list_exercises(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plan_id: Optional[uuid.UUID] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_exercises(user_id, pagination, plan_id))


@router.get("/exercises/{exercise_id}", response_model=APIResponse[ExerciseResponse])
async def get_exercise(
    exercise_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ExerciseResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_exercise(exercise_id, user_id))


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


@router.post("/sessions", response_model=APIResponse[SessionResponse])
async def create_session(
    data: SessionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SessionResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.create_session(user_id, data))


@router.get("/sessions", response_model=APIResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plan_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = WorkoutService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(
        data=await service.list_sessions(user_id, pagination, plan_id, start_date, end_date)
    )


@router.get("/sessions/{session_id}", response_model=APIResponse[SessionResponse])
async def get_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SessionResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_session(session_id, user_id))


@router.patch("/sessions/{session_id}", response_model=APIResponse[SessionResponse])
async def update_session(
    session_id: uuid.UUID,
    data: SessionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SessionResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.update_session(session_id, user_id, data))


@router.delete("/sessions/{session_id}", response_model=APIResponse[None])
async def delete_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = WorkoutService(db)
    await service.delete_session(session_id, user_id)
    return APIResponse(data=None)


@router.post("/sessions/{session_id}/sets", response_model=APIResponse[WorkoutSetResponse])
async def add_set(
    session_id: uuid.UUID,
    data: WorkoutSetCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WorkoutSetResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.add_set(session_id, user_id, data))


@router.get("/profile", response_model=APIResponse[ProfileResponse])
async def get_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProfileResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_profile(user_id))


@router.put("/profile", response_model=APIResponse[ProfileResponse])
async def update_profile(
    data: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProfileResponse]:
    service = WorkoutService(db)
    return APIResponse(data=await service.update_profile(user_id, data))


@router.get("/summary/weekly-volume", response_model=APIResponse[WeeklyVolumeSummary])
async def get_weekly_volume(
    reference_date: Optional[date] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WeeklyVolumeSummary]:
    service = WorkoutService(db)
    return APIResponse(data=await service.get_weekly_volume(user_id, reference_date))
