"""AI memory models."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MemoryType(str, enum.Enum):
    GOAL = "goal"
    PREFERENCE = "preference"
    HABIT = "habit"
    PATTERN = "pattern"
    STUDY = "study"
    WORKOUT = "workout"
    FINANCIAL = "financial"
    EMOTIONAL = "emotional"
    ROUTINE = "routine"
    FACT = "fact"


class AIMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    type: Mapped[MemoryType] = mapped_column(Enum(MemoryType, name="memory_type"), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AINote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_notes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=5)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)


class DailyJournal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "daily_journal"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mood_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    energy_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    productivity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    study_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workout_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habit_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    important_events: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WeeklyReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "weekly_reviews"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    week_reference: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wins: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    patterns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EntityRelation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simplified knowledge graph."""

    __tablename__ = "entity_relations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    source_entity: Mapped[str] = mapped_column(String(255), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
