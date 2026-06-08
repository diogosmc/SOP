"""Study models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class TopicStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    MASTERED = "mastered"


class ReviewRating(str, enum.Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class StudySubject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "study_subjects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    user: Mapped["User"] = relationship(back_populates="study_subjects")
    topics: Mapped[list["StudyTopic"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["StudySession"]] = relationship(back_populates="subject")


class StudyTopic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "study_topics"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TopicStatus] = mapped_column(
        Enum(TopicStatus, name="study_topic_status", values_callable=lambda x: [e.value for e in x]),
        default=TopicStatus.NOT_STARTED,
        index=True,
        nullable=False,
    )
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    subject: Mapped["StudySubject"] = relationship(back_populates="topics")
    flashcards: Mapped[list["Flashcard"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["StudySession"]] = relationship(back_populates="topic")


class Flashcard(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "flashcards"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("2.50"), nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    topic: Mapped["StudyTopic"] = relationship(back_populates="flashcards")


class StudySession(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "study_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_subjects.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_topics.id", ondelete="SET NULL"), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    technique: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="study_sessions")
    subject: Mapped[Optional["StudySubject"]] = relationship(back_populates="sessions")
    topic: Mapped[Optional["StudyTopic"]] = relationship(back_populates="sessions")
