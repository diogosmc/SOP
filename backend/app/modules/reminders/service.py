"""Reminder business logic."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.reminders.models import ReminderStatus
from app.modules.reminders.repository import ReminderRepository
from app.modules.reminders.schemas import ReminderCreate, ReminderResponse, ReminderUpdate


class ReminderService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ReminderRepository(db)

    async def create(
        self, user_id: uuid.UUID, data: ReminderCreate
    ) -> ReminderResponse:
        reminder = await self.repo.create(user_id, data)
        return ReminderResponse.model_validate(reminder)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        status_filter: Optional[ReminderStatus] = None,
    ) -> PaginatedResponse[ReminderResponse]:
        items, total = await self.repo.list_reminders(
            user_id, status_filter, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [ReminderResponse.model_validate(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, reminder_id: uuid.UUID, user_id: uuid.UUID, data: ReminderUpdate
    ) -> ReminderResponse:
        reminder = await self.repo.get_by_id(reminder_id, user_id)
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
            )
        updated = await self.repo.update(reminder, data)
        return ReminderResponse.model_validate(updated)

    async def delete(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        reminder = await self.repo.get_by_id(reminder_id, user_id)
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
            )
        await self.repo.delete(reminder)

    async def cancel(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> ReminderResponse:
        reminder = await self.repo.get_by_id(reminder_id, user_id)
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
            )
        reminder.status = ReminderStatus.CANCELLED
        await self.repo.db.flush()
        await self.repo.db.refresh(reminder)
        return ReminderResponse.model_validate(reminder)

    async def mark_sent(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> ReminderResponse:
        reminder = await self.repo.get_by_id(reminder_id, user_id)
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
            )
        reminder.status = ReminderStatus.SENT
        await self.repo.db.flush()
        await self.repo.db.refresh(reminder)
        return ReminderResponse.model_validate(reminder)

    async def get_due_reminders(
        self, user_id: uuid.UUID, now: Optional[datetime] = None
    ) -> List[ReminderResponse]:
        reminders = await self.repo.get_due_reminders(user_id, now)
        return [ReminderResponse.model_validate(item) for item in reminders]

    async def list_pending(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[ReminderResponse]:
        return await self.list(user_id, pagination, ReminderStatus.PENDING)
