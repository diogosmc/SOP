"""Task repository."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import Task, TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: TaskCreate) -> Task:
        task = Task(user_id=user_id, **data.model_dump())
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Task]:
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        query = select(Task).where(Task.user_id == user_id)
        count_query = select(func.count()).select_from(Task).where(Task.user_id == user_id)
        if status is not None:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(task, field, value)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.flush()
