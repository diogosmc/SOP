"""Tests for main SQLAlchemy models and Alembic metadata registration."""

import importlib

import pytest

from app.db.base import Base
from app.db import models as db_models

EXPECTED_TABLES = {
    "users",
    "tasks",
    "habits",
    "habit_logs",
    "notes",
    "documents",
    "document_chunks",
    "chat_sessions",
    "chat_messages",
    "ai_memories",
    "ai_notes",
    "daily_journal",
    "reminders",
    "finance_transactions",
    "study_subjects",
    "study_topics",
    "flashcards",
    "study_sessions",
    "workout_profiles",
    "exercises",
    "workout_plans",
    "workout_logs",
    "exercise_set_logs",
}

VECTOR_TABLES = {
    "document_chunks": "embedding",
    "ai_memories": "embedding",
    "ai_notes": "embedding",
}


def test_import_all_models_module() -> None:
    importlib.reload(db_models)
    assert db_models.Base is Base


def test_all_main_tables_registered_on_metadata() -> None:
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Missing tables in metadata: {missing}"


def test_all_models_have_uuid_primary_key() -> None:
    for table_name in EXPECTED_TABLES:
        pk = Base.metadata.tables[table_name].c.id
        assert pk.primary_key is True
        assert "UUID" in str(pk.type)


def test_all_models_have_created_at() -> None:
    for table_name in EXPECTED_TABLES:
        assert "created_at" in Base.metadata.tables[table_name].c


def test_vector_columns_dimension_768() -> None:
    for table_name, column_name in VECTOR_TABLES.items():
        column = Base.metadata.tables[table_name].c[column_name]
        assert "768" in str(column.type)


@pytest.mark.integration
def test_database_tables_exist_after_migration(postgres_url: str) -> None:
    import sqlalchemy as sa

    engine = sa.create_engine(postgres_url.replace("+asyncpg", ""))
    with engine.connect() as conn:
        result = conn.execute(
            sa.text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                """
            )
        )
        tables = {row[0] for row in result}
    engine.dispose()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables in database: {missing}"


@pytest.mark.integration
def test_vector_columns_in_database(postgres_url: str) -> None:
    import sqlalchemy as sa

    engine = sa.create_engine(postgres_url.replace("+asyncpg", ""))
    with engine.connect() as conn:
        for table_name, column_name in VECTOR_TABLES.items():
            result = conn.execute(
                sa.text(
                    """
                    SELECT format_type(a.atttypid, a.atttypmod)
                    FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = 'public'
                      AND c.relname = :table
                      AND a.attname = :column
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                    """
                ),
                {"table": table_name, "column": column_name},
            )
            row = result.one()
            assert row[0] == "vector(768)"
    engine.dispose()
