"""User model."""

import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.chat.models import ChatSession
    from app.modules.finance.models import FinanceTransaction
    from app.modules.habits.models import Habit
    from app.modules.memory.models import AIMemory, AINote, DailyJournal
    from app.modules.notes.models import Document, DocumentChunk, Note
    from app.modules.reminders.models import Reminder
    from app.modules.study.models import Flashcard, StudySession, StudySubject, StudyTopic
    from app.modules.tasks.models import Task
    from app.modules.workout.models import Exercise, WorkoutLog, WorkoutPlan, WorkoutProfile


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="America/Sao_Paulo",
        server_default="America/Sao_Paulo",
    )
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    habits: Mapped[list["Habit"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_memories: Mapped[list["AIMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_notes: Mapped[list["AINote"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    daily_journals: Mapped[list["DailyJournal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    finance_transactions: Mapped[list["FinanceTransaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    study_subjects: Mapped[list["StudySubject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    workout_profile: Mapped[Optional["WorkoutProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
