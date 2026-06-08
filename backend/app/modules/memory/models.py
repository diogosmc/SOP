"""AI memory models."""

import enum
import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


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
    OTHER = "other"


class AIMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[MemoryType] = mapped_column(
        Enum(
            MemoryType,
            name="memory_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(768), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="ai_memories")


class AINote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_notes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(768), nullable=True)

    user: Mapped["User"] = relationship(back_populates="ai_notes")


class DailyJournal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "daily_journal"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_journal_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mood_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    energy_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    productivity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    study_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workout_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habit_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    important_events: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    user: Mapped["User"] = relationship(back_populates="daily_journals")
