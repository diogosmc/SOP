"""Habit schemas."""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.habits.models import HabitType


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    habit_type: HabitType = HabitType.POSITIVE
    is_active: bool = True
    target_days_per_week: int = Field(default=7, ge=1, le=7)


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    habit_type: Optional[HabitType] = None
    is_active: Optional[bool] = None
    target_days_per_week: Optional[int] = Field(default=None, ge=1, le=7)


class HabitResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    habit_type: HabitType
    is_active: bool
    target_days_per_week: int
    current_streak: int
    max_streak: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HabitLogCreate(BaseModel):
    log_date: date = Field(default_factory=date.today)
    completed: bool = True
    notes: Optional[str] = None


class HabitLogResponse(BaseModel):
    id: uuid.UUID
    habit_id: uuid.UUID
    user_id: uuid.UUID
    log_date: date
    completed: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    current_streak: int
    max_streak: int

    model_config = {"from_attributes": True}
