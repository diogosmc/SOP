"""Habit models."""

import enum
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class HabitType(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class HabitLogStatus(str, enum.Enum):
    DONE = "done"
    FAILED = "failed"
    AVOIDED = "avoided"


class Habit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "habits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[HabitType] = mapped_column(
        Enum(HabitType, name="habit_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    streak_current: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_best: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="habits")
    logs: Mapped[list["HabitLog"]] = relationship(back_populates="habit", cascade="all, delete-orphan")


class HabitLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "date", name="uq_habit_log_habit_date"),)

    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[HabitLogStatus] = mapped_column(
        Enum(HabitLogStatus, name="habit_log_status"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    habit: Mapped["Habit"] = relationship(back_populates="logs")
