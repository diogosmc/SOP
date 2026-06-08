"""Workout module tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_workout_models"
down_revision: Union[str, None] = "004_study_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    workout_objective = postgresql.ENUM(
        "hypertrophy", "fat_loss", "strength", "health", "other",
        name="workout_objective", create_type=True,
    )
    exercise_type = postgresql.ENUM(
        "strength", "cardio", "mobility", "functional",
        name="exercise_type", create_type=True,
    )

    op.create_table(
        "workout_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("height_cm", sa.Numeric(5, 1), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 1), nullable=True),
        sa.Column("objective", workout_objective, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workout_profiles_user_id", "workout_profiles", ["user_id"], unique=True)

    op.create_table(
        "exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("muscle_group", sa.String(100), nullable=True),
        sa.Column("exercise_type", exercise_type, nullable=False, server_default="strength"),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_exercises_user_id", "exercises", ["user_id"])

    op.create_table(
        "workout_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.String(100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workout_plans_user_id", "workout_plans", ["user_id"])
    op.create_index("ix_workout_plans_active", "workout_plans", ["active"])

    op.create_table(
        "workout_plan_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_label", sa.String(50), nullable=True),
        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("reps", sa.String(50), nullable=True),
        sa.Column("target_load_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_workout_plan_exercises_plan_id", "workout_plan_exercises", ["plan_id"])

    op.create_table(
        "workout_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workout_logs_user_id", "workout_logs", ["user_id"])
    op.create_index("ix_workout_logs_date", "workout_logs", ["date"])

    op.create_table(
        "exercise_set_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workout_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("load_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_exercise_set_logs_workout_log_id", "exercise_set_logs", ["workout_log_id"])


def downgrade() -> None:
    op.drop_index("ix_exercise_set_logs_workout_log_id", table_name="exercise_set_logs")
    op.drop_table("exercise_set_logs")
    op.drop_index("ix_workout_logs_date", table_name="workout_logs")
    op.drop_index("ix_workout_logs_user_id", table_name="workout_logs")
    op.drop_table("workout_logs")
    op.drop_index("ix_workout_plan_exercises_plan_id", table_name="workout_plan_exercises")
    op.drop_table("workout_plan_exercises")
    op.drop_index("ix_workout_plans_active", table_name="workout_plans")
    op.drop_index("ix_workout_plans_user_id", table_name="workout_plans")
    op.drop_table("workout_plans")
    op.drop_index("ix_exercises_user_id", table_name="exercises")
    op.drop_table("exercises")
    op.drop_index("ix_workout_profiles_user_id", table_name="workout_profiles")
    op.drop_table("workout_profiles")
    op.execute("DROP TYPE IF EXISTS exercise_type")
    op.execute("DROP TYPE IF EXISTS workout_objective")
