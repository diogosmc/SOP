"""Task service."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.tasks.models import TaskStatus
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskResponse, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = TaskRepository(db)

    async def create(self, user_id: uuid.UUID, data: TaskCreate) -> TaskResponse:
        task = await self.repo.create(user_id, data)
        return TaskResponse.model_validate(task)

    async def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskResponse:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return TaskResponse.model_validate(task)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        status_filter: Optional[TaskStatus] = None,
    ) -> PaginatedResponse[TaskResponse]:
        items, total = await self.repo.list(
            user_id, status_filter, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [TaskResponse.model_validate(t) for t in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, task_id: uuid.UUID, user_id: uuid.UUID, data: TaskUpdate
    ) -> TaskResponse:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        updated = await self.repo.update(task, data)
        return TaskResponse.model_validate(updated)

    async def delete(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        await self.repo.delete(task)
