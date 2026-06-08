"""Reminder API schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.reminders.models import ReminderChannel, ReminderStatus


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    remind_at: datetime
    recurring: bool = False
    recurrence_rule: Optional[str] = Field(default=None, max_length=255)
    channel: ReminderChannel = ReminderChannel.BOTH


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    remind_at: Optional[datetime] = None
    recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = Field(default=None, max_length=255)
    channel: Optional[ReminderChannel] = None
    status: Optional[ReminderStatus] = None


class ReminderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    remind_at: datetime
    recurring: bool
    recurrence_rule: Optional[str]
    channel: ReminderChannel
    status: ReminderStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
