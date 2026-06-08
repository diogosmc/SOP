"""Workout schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=10)
    description: Optional[str] = None
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=10)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExerciseCreate(BaseModel):
    plan_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    default_sets: int = Field(default=3, ge=1)
    default_reps: int = Field(default=10, ge=1)


class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    default_sets: Optional[int] = Field(default=None, ge=1)
    default_reps: Optional[int] = Field(default=None, ge=1)


class ExerciseResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    muscle_group: Optional[str]
    default_sets: int
    default_reps: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkoutSetCreate(BaseModel):
    exercise_id: uuid.UUID
    set_number: int = Field(default=1, ge=1)
    reps: int = Field(ge=0)
    weight_kg: Decimal = Field(default=Decimal("0"), ge=0)


class WorkoutSetResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    exercise_id: uuid.UUID
    user_id: uuid.UUID
    set_number: int
    reps: int
    weight_kg: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    plan_id: Optional[uuid.UUID] = None
    session_date: date
    notes: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    sets: List[WorkoutSetCreate] = Field(default_factory=list)


class SessionUpdate(BaseModel):
    plan_id: Optional[uuid.UUID] = None
    session_date: Optional[date] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan_id: Optional[uuid.UUID]
    session_date: date
    notes: Optional[str]
    duration_minutes: Optional[int]
    sets: List[WorkoutSetResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    weight_kg: Optional[Decimal] = Field(default=None, gt=0)
    height_m: Optional[Decimal] = Field(default=None, gt=0)
    body_fat_pct: Optional[Decimal] = Field(default=None, ge=0, le=100)
    goal: Optional[str] = Field(default=None, max_length=255)


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    weight_kg: Optional[Decimal]
    height_m: Optional[Decimal]
    body_fat_pct: Optional[Decimal]
    goal: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MuscleVolume(BaseModel):
    muscle_group: str
    total_sets: int
    total_reps: int
    total_volume_kg: Decimal


class WeeklyVolumeSummary(BaseModel):
    week_start: date
    week_end: date
    total_sessions: int
    total_sets: int
    total_reps: int
    total_volume_kg: Decimal
    by_muscle_group: List[MuscleVolume]
