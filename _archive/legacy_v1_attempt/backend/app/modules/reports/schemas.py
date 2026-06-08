"""Reports schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class DailyReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: datetime
    summary: Optional[str]
    mood_score: Optional[int]
    energy_score: Optional[int]
    productivity_score: Optional[int]
    study_summary: Optional[str]
    workout_summary: Optional[str]
    finance_summary: Optional[str]
    habit_summary: Optional[str]
    important_events: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WeeklyReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_reference: str
    summary: Optional[str]
    wins: Optional[str]
    failures: Optional[str]
    patterns: Optional[str]
    recommendations: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateWeeklyRequest(BaseModel):
    week_reference: Optional[str] = Field(
        default=None,
        description="ISO week reference, e.g. 2026-W23. Defaults to current week.",
    )


class ModuleAnalytics(BaseModel):
    module: str
    metrics: dict[str, Any]


class AnalyticsResponse(BaseModel):
    period_start: date
    period_end: date
    modules: List[ModuleAnalytics]
    insights: dict[str, Any]


class FinanceAnalytics(BaseModel):
    income: Decimal
    expense: Decimal
    balance: Decimal
    transaction_count: int


class StudyAnalytics(BaseModel):
    total_minutes: int
    session_count: int
    topics_mastered: int
    flashcard_count: int


class WorkoutAnalytics(BaseModel):
    session_count: int
    total_sets: int
    total_volume_kg: Decimal


class TasksAnalytics(BaseModel):
    completed: int
    pending: int
    completion_rate: float


class HabitsAnalytics(BaseModel):
    active_habits: int
    completions: int
    adherence_rate: float
