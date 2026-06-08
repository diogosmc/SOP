"""Habit models."""

import enum
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HabitType(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class Habit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "habits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habit_type: Mapped[HabitType] = mapped_column(
        Enum(HabitType, name="habit_type"), default=HabitType.POSITIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_days_per_week: Mapped[int] = mapped_column(Integer, default=7)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)


class HabitLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),)

    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
