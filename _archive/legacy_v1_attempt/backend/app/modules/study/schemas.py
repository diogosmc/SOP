"""Study schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.modules.study.models import TopicStatus


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    color: Optional[str] = Field(default=None, max_length=20)
    sort_order: int = 0


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    color: Optional[str] = Field(default=None, max_length=20)
    sort_order: Optional[int] = None


class SubjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicCreate(BaseModel):
    subject_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    status: TopicStatus = TopicStatus.NOT_STARTED
    notes: Optional[str] = None


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    status: Optional[TopicStatus] = None
    notes: Optional[str] = None
    study_plan: Optional[dict[str, Any]] = None


class TopicResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    status: TopicStatus
    notes: Optional[str]
    study_plan: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlashcardCreate(BaseModel):
    topic_id: uuid.UUID
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class FlashcardUpdate(BaseModel):
    front: Optional[str] = Field(default=None, min_length=1)
    back: Optional[str] = Field(default=None, min_length=1)
    ease_factor: Optional[float] = None
    interval_days: Optional[int] = None
    repetitions: Optional[int] = None
    next_review: Optional[datetime] = None


class FlashcardResponse(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    user_id: uuid.UUID
    front: str
    back: str
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudySessionCreate(BaseModel):
    topic_id: Optional[uuid.UUID] = None
    duration_minutes: int = Field(default=0, ge=0)
    questions_count: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class StudySessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: Optional[uuid.UUID]
    duration_minutes: int
    questions_count: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanWithAIRequest(BaseModel):
    focus_areas: Optional[str] = None
    available_hours: Optional[int] = Field(default=None, ge=1, le=40)


class PlanWithAIResponse(BaseModel):
    topic_id: uuid.UUID
    study_plan: dict[str, Any]
