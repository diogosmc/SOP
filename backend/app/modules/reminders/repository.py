"""Reminder persistence."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reminders.models import Reminder, ReminderStatus
from app.modules.reminders.schemas import ReminderCreate, ReminderUpdate


class ReminderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: ReminderCreate) -> Reminder:
        payload = data.model_dump()
        payload["channel"] = data.channel.value
        reminder = Reminder(user_id=user_id, **payload)
        self.db.add(reminder)
        await self.db.flush()
        await self.db.refresh(reminder)
        return reminder

    async def get_by_id(
        self, reminder_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Reminder]:
        result = await self.db.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_reminders(
        self,
        user_id: uuid.UUID,
        status: Optional[ReminderStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Reminder], int]:
        query = select(Reminder).where(Reminder.user_id == user_id)
        count_query = (
            select(func.count()).select_from(Reminder).where(Reminder.user_id == user_id)
        )
        if status:
            query = query.where(Reminder.status == status)
            count_query = count_query.where(Reminder.status == status)

        query = query.order_by(Reminder.remind_at.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(self, reminder: Reminder, data: ReminderUpdate) -> Reminder:
        payload = data.model_dump(exclude_unset=True)
        if "channel" in payload and payload["channel"] is not None:
            payload["channel"] = payload["channel"].value
        if "status" in payload and payload["status"] is not None:
            payload["status"] = payload["status"].value
        for key, value in payload.items():
            setattr(reminder, key, value)
        await self.db.flush()
        await self.db.refresh(reminder)
        return reminder

    async def delete(self, reminder: Reminder) -> None:
        await self.db.delete(reminder)
        await self.db.flush()

    async def get_due_reminders(
        self,
        user_id: uuid.UUID,
        now: Optional[datetime] = None,
    ) -> List[Reminder]:
        current = now or datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Reminder)
            .where(
                Reminder.user_id == user_id,
                Reminder.status == ReminderStatus.PENDING,
                Reminder.remind_at <= current,
            )
            .order_by(Reminder.remind_at.asc())
        )
        return list(result.scalars().all())
