"""Task API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.tasks.models import TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=APIResponse[TaskResponse])
async def create_task(
    data: TaskCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TaskResponse]:
    service = TaskService(db)
    return APIResponse(data=await service.create(user_id, data))


@router.get("", response_model=APIResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = TaskService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list(user_id, pagination, status))


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TaskResponse]:
    service = TaskService(db)
    return APIResponse(data=await service.get(task_id, user_id))


@router.patch("/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TaskResponse]:
    service = TaskService(db)
    return APIResponse(data=await service.update(task_id, user_id, data))


@router.delete("/{task_id}", response_model=APIResponse[None])
async def delete_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = TaskService(db)
    await service.delete(task_id, user_id)
    return APIResponse(data=None)
