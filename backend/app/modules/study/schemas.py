"""Study schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.study.models import ReviewRating, TopicStatus


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=32)


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=32)


class SubjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicCreate(BaseModel):
    subject_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    content: Optional[str] = None
    status: TopicStatus = TopicStatus.NOT_STARTED
    difficulty: int = Field(default=3, ge=1, le=5)
    next_review: Optional[datetime] = None


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content: Optional[str] = None
    status: Optional[TopicStatus] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    next_review: Optional[datetime] = None


class TopicResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    content: Optional[str]
    status: TopicStatus
    difficulty: int
    next_review: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlashcardCreate(BaseModel):
    topic_id: uuid.UUID
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class FlashcardResponse(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    front: str
    back: str
    next_review: Optional[datetime]
    interval_days: int
    ease_factor: Decimal
    repetitions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlashcardReviewRequest(BaseModel):
    rating: ReviewRating


class SessionCreate(BaseModel):
    subject_id: Optional[uuid.UUID] = None
    topic_id: Optional[uuid.UUID] = None
    duration_minutes: int = Field(ge=1, le=600)
    technique: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_id: Optional[uuid.UUID]
    topic_id: Optional[uuid.UUID]
    duration_minutes: int
    technique: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class StudySummary(BaseModel):
    total_subjects: int
    total_topics: int
    topics_in_progress: int
    topics_mastered: int
    flashcards_due: int
    minutes_studied_today: int
    minutes_studied_week: int


class AIPlanResponse(BaseModel):
    topic_id: uuid.UUID
    plan: str


class SM2State(BaseModel):
    interval_days: int
    ease_factor: Decimal
    repetitions: int
