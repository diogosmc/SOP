"""Performance indexes — composite filters and pgvector HNSW."""

from typing import Sequence, Union

from alembic import op

revision: str = "007_performance_indexes"
down_revision: Union[str, None] = "006_user_auth_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite indexes for common list/filter queries
    op.create_index(
        "ix_tasks_user_status_due",
        "tasks",
        ["user_id", "status", "due_date"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_habits_user_active_type",
        "habits",
        ["user_id", "active", "type"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_notes_user_favorite_archived",
        "notes",
        ["user_id", "favorite", "archived"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_notes_user_created_at",
        "notes",
        ["user_id", "created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_finance_tx_user_date_type_cat",
        "finance_transactions",
        ["user_id", "transaction_date", "type", "category"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_study_sessions_user_created",
        "study_sessions",
        ["user_id", "created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_workout_logs_user_date",
        "workout_logs",
        ["user_id", "date"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_ai_memories_user_type_importance",
        "ai_memories",
        ["user_id", "type", "importance"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_reminders_user_remind_status",
        "reminders",
        ["user_id", "remind_at", "status"],
        unique=False,
        if_not_exists=True,
    )

    # pgvector HNSW — safe on empty/small tables; requires pgvector 0.5+
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_memories_embedding_hnsw
        ON ai_memories USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_notes_embedding_hnsw
        ON ai_notes USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ai_notes_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_ai_memories_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")

    op.drop_index("ix_reminders_user_remind_status", table_name="reminders", if_exists=True)
    op.drop_index("ix_ai_memories_user_type_importance", table_name="ai_memories", if_exists=True)
    op.drop_index("ix_chat_messages_session_created", table_name="chat_messages", if_exists=True)
    op.drop_index("ix_workout_logs_user_date", table_name="workout_logs", if_exists=True)
    op.drop_index("ix_study_sessions_user_created", table_name="study_sessions", if_exists=True)
    op.drop_index("ix_finance_tx_user_date_type_cat", table_name="finance_transactions", if_exists=True)
    op.drop_index("ix_notes_user_created_at", table_name="notes", if_exists=True)
    op.drop_index("ix_notes_user_favorite_archived", table_name="notes", if_exists=True)
    op.drop_index("ix_habits_user_active_type", table_name="habits", if_exists=True)
    op.drop_index("ix_tasks_user_status_due", table_name="tasks", if_exists=True)
