"""Study module tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_study_models"
down_revision: Union[str, None] = "003_finance_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    study_topic_status = postgresql.ENUM(
        "not_started",
        "in_progress",
        "review",
        "mastered",
        name="study_topic_status",
        create_type=True,
    )

    op.create_table(
        "study_subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_study_subjects_user_id", "study_subjects", ["user_id"])

    op.create_table(
        "study_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("study_subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", study_topic_status, nullable=False, server_default="not_started"),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_study_topics_subject_id", "study_topics", ["subject_id"])
    op.create_index("ix_study_topics_status", "study_topics", ["status"])

    op.create_table(
        "flashcards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("study_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("next_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ease_factor", sa.Numeric(4, 2), nullable=False, server_default="2.50"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_flashcards_topic_id", "flashcards", ["topic_id"])
    op.create_index("ix_flashcards_next_review", "flashcards", ["next_review"])

    op.create_table(
        "study_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("study_subjects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("study_topics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("technique", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_study_sessions_user_id", "study_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_study_sessions_user_id", table_name="study_sessions")
    op.drop_table("study_sessions")
    op.drop_index("ix_flashcards_next_review", table_name="flashcards")
    op.drop_index("ix_flashcards_topic_id", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_index("ix_study_topics_status", table_name="study_topics")
    op.drop_index("ix_study_topics_subject_id", table_name="study_topics")
    op.drop_table("study_topics")
    op.drop_index("ix_study_subjects_user_id", table_name="study_subjects")
    op.drop_table("study_subjects")
    op.execute("DROP TYPE IF EXISTS study_topic_status")
