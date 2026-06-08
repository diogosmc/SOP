"""Tests for daily journal updates."""

import pytest
from httpx import AsyncClient

from app.ai.memory.classifier import classify_message
from app.ai.memory.journal import _today, update_daily_journal_from_message
from app.modules.memory.repository import MemoryRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_daily_journal_created_and_updated(db_session, default_user_id) -> None:
    message = "Estudei Python por 2 horas hoje"
    classification = classify_message(message)

    await update_daily_journal_from_message(
        default_user_id, message, classification, db_session
    )
    await update_daily_journal_from_message(
        default_user_id,
        "Gastei 30 no almoço",
        classify_message("Gastei 30 no almoço"),
        db_session,
    )

    repo = MemoryRepository(db_session)
    journal = await repo.get_journal_by_date(default_user_id, _today())
    assert journal is not None
    assert journal.summary
    assert journal.study_summary
    assert journal.finance_summary


@pytest.mark.integration
@pytest.mark.asyncio
async def test_journal_today_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/memory/journal/today")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "date" in data
    assert "important_events" in data

    rebuild = await client.post("/api/v1/memory/journal/rebuild-today")
    assert rebuild.status_code == 200
