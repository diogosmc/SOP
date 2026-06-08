"""Habit schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.habits.models import HabitType


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    type: HabitType
    frequency: Optional[str] = Field(default=None, max_length=50)
    active: bool = True


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[HabitType] = None
    frequency: Optional[str] = Field(default=None, max_length=50)
    active: Optional[bool] = None


class HabitResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    type: HabitType
    frequency: Optional[str]
    streak_current: int
    streak_best: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
