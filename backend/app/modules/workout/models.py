"""Workout models."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class WorkoutObjective(str, enum.Enum):
    HYPERTROPHY = "hypertrophy"
    FAT_LOSS = "fat_loss"
    STRENGTH = "strength"
    HEALTH = "health"
    OTHER = "other"


class ExerciseType(str, enum.Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    MOBILITY = "mobility"
    FUNCTIONAL = "functional"


class WorkoutProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workout_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    objective: Mapped[Optional[WorkoutObjective]] = mapped_column(
        Enum(WorkoutObjective, name="workout_objective", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="workout_profile")


class Exercise(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "exercises"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    muscle_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(
        Enum(ExerciseType, name="exercise_type", values_callable=lambda x: [e.value for e in x]),
        default=ExerciseType.STRENGTH,
        nullable=False,
    )
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="exercises")


class WorkoutPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workout_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="workout_plans")
    plan_exercises: Mapped[list["WorkoutPlanExercise"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    logs: Mapped[list["WorkoutLog"]] = relationship(back_populates="plan")


class WorkoutPlanExercise(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "workout_plan_exercises"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_load_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="plan_exercises")
    exercise: Mapped["Exercise"] = relationship()


class WorkoutLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workout_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="workout_logs")
    plan: Mapped[Optional["WorkoutPlan"]] = relationship(back_populates="logs")
    set_logs: Mapped[list["ExerciseSetLog"]] = relationship(
        back_populates="workout_log", cascade="all, delete-orphan"
    )


class ExerciseSetLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "exercise_set_logs"

    workout_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workout_logs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), index=True, nullable=False
    )
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    load_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workout_log: Mapped["WorkoutLog"] = relationship(back_populates="set_logs")
    exercise: Mapped["Exercise"] = relationship()
