"""Workout schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.workout.models import ExerciseType, WorkoutObjective


class ProfileUpdate(BaseModel):
    height_cm: Optional[Decimal] = Field(default=None, ge=0)
    weight_kg: Optional[Decimal] = Field(default=None, ge=0)
    objective: Optional[WorkoutObjective] = None
    notes: Optional[str] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    height_cm: Optional[Decimal]
    weight_kg: Optional[Decimal]
    objective: Optional[WorkoutObjective]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExerciseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    exercise_type: ExerciseType = ExerciseType.STRENGTH
    instructions: Optional[str] = None


class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    exercise_type: Optional[ExerciseType] = None
    instructions: Optional[str] = None


class ExerciseResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    name: str
    muscle_group: Optional[str]
    exercise_type: ExerciseType
    instructions: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    objective: Optional[str] = Field(default=None, max_length=100)
    active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    objective: Optional[str] = Field(default=None, max_length=100)
    active: Optional[bool] = None


class PlanExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    day_label: Optional[str] = Field(default=None, max_length=50)
    sets: Optional[int] = Field(default=None, ge=1)
    reps: Optional[str] = Field(default=None, max_length=50)
    target_load_kg: Optional[Decimal] = Field(default=None, ge=0)
    rest_seconds: Optional[int] = Field(default=None, ge=0)
    order_index: int = 0
    notes: Optional[str] = None


class PlanExerciseResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    exercise_id: uuid.UUID
    exercise_name: Optional[str] = None
    day_label: Optional[str]
    sets: Optional[int]
    reps: Optional[str]
    target_load_kg: Optional[Decimal]
    rest_seconds: Optional[int]
    order_index: int
    notes: Optional[str]

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    objective: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanDetailResponse(PlanResponse):
    exercises: List[PlanExerciseResponse] = []


class LogCreate(BaseModel):
    plan_id: Optional[uuid.UUID] = None
    date: date
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=600)
    notes: Optional[str] = None
    completed: bool = True


class LogUpdate(BaseModel):
    plan_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=600)
    notes: Optional[str] = None
    completed: Optional[bool] = None


class SetLogCreate(BaseModel):
    exercise_id: uuid.UUID
    set_number: int = Field(ge=1)
    reps: int = Field(ge=0)
    load_kg: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None


class SetLogResponse(BaseModel):
    id: uuid.UUID
    workout_log_id: uuid.UUID
    exercise_id: uuid.UUID
    exercise_name: Optional[str] = None
    set_number: int
    reps: int
    load_kg: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan_id: Optional[uuid.UUID]
    date: date
    duration_minutes: Optional[int]
    notes: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime
    sets: List[SetLogResponse] = []

    model_config = {"from_attributes": True}


class WorkoutSummary(BaseModel):
    workouts_this_week: int
    workouts_this_month: int
    total_volume_week: Decimal
    last_workout_date: Optional[date]
    active_plan: Optional[str]
    completed_rate: float


class ProgressionPoint(BaseModel):
    date: date
    exercise_id: uuid.UUID
    exercise_name: str
    load_kg: Optional[Decimal]
    reps: int
    set_number: int
