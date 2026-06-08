"""Reports schemas."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class DailyReport(BaseModel):
    date: date
    tasks_completed: int
    tasks_pending: int
    habits_active: int
    study_minutes: int
    workout_completed: bool
    income: Decimal
    expense: Decimal
    balance: Decimal
    mood_score: Optional[int] = None
    productivity_score: Optional[float] = None
    summary: Optional[str] = None


class WeeklyReport(BaseModel):
    week_start: date
    week_end: date
    tasks_completed: int
    study_minutes: int
    workouts_completed: int
    finance_balance: Decimal
    habits_summary: str
    wins: List[str] = Field(default_factory=list)
    problems: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CategoryAmount(BaseModel):
    category: str
    income: Decimal
    expense: Decimal
    total: Decimal


class DayAmount(BaseModel):
    date: date
    value: int


class DayFinance(BaseModel):
    date: date
    income: Decimal
    expense: Decimal
    balance: Decimal


class HabitsAnalytics(BaseModel):
    active: int
    positive: int
    negative: int


class AnalyticsResponse(BaseModel):
    period_start: date
    period_end: date
    tasks_by_status: dict[str, int]
    finance_by_category: List[CategoryAmount]
    study_minutes_by_day: List[DayAmount]
    workouts_by_day: List[DayAmount]
    habits: HabitsAnalytics
    memories_by_type: dict[str, int]


class InsightsResponse(BaseModel):
    insights: List[str]
    source: str
    ai_used: bool = False


class RebuildDailyResponse(BaseModel):
    rebuilt: bool
    report: DailyReport
