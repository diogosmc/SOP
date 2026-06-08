"""Memory module API schemas."""

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.modules.memory.models import MemoryType


class AIMemoryCreate(BaseModel):
    type: MemoryType
    content: str = Field(min_length=1)
    importance: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source: Optional[str] = Field(default=None, max_length=100)
    expires_at: Optional[datetime] = None


class AIMemoryUpdate(BaseModel):
    type: Optional[MemoryType] = None
    content: Optional[str] = Field(default=None, min_length=1)
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source: Optional[str] = Field(default=None, max_length=100)
    expires_at: Optional[datetime] = None


class AIMemoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: MemoryType
    content: str
    importance: int
    confidence: float
    source: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AINoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    category: Optional[str] = Field(default=None, max_length=100)
    importance: int = Field(default=5, ge=1, le=10)


class AINoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    category: Optional[str]
    importance: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyJournalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    summary: Optional[str]
    mood_score: Optional[int]
    energy_score: Optional[int]
    productivity_score: Optional[int]
    study_summary: Optional[str]
    workout_summary: Optional[str]
    finance_summary: Optional[str]
    habit_summary: Optional[str]
    important_events: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
