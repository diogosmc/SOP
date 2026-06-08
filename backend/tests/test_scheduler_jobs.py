"""Tests for scheduler jobs, notifications and summaries."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.memory.journal import update_daily_journal_from_message
from app.ai.memory.classifier import classify_message
from app.modules.reminders.schemas import ReminderCreate
from app.modules.reminders.service import ReminderService
from app.scheduler.app import reset_scheduler
from app.scheduler.jobs import (
    process_due_reminders,
    process_pending_embeddings_stub,
    send_checkin,
    send_daily_summary_job,
)
from app.scheduler.notifications import send_notification
from app.scheduler.summaries import build_daily_summary


@pytest.fixture(autouse=True)
def _clean_scheduler() -> None:
    reset_scheduler()
    yield
    reset_scheduler()


@pytest.mark.asyncio
async def test_notification_telegram_disabled_does_not_break(caplog) -> None:
    with patch("app.scheduler.notifications.get_settings") as mock_settings:
        from app.core.config import Settings

        mock_settings.return_value = Settings(telegram_enabled=False)
        result = await send_notification("Teste de notificação")
    assert result is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_daily_summary(db_session, default_user_id) -> None:
    message = "Estudei Python hoje"
    classification = classify_message(message)
    await update_daily_journal_from_message(
        default_user_id, message, classification, db_session
    )

    summary = await build_daily_summary(default_user_id, db_session)
    assert "Resumo de" in summary
    assert "Python" in summary or "Estudo" in summary or "estudo" in summary.lower()


@pytest.mark.asyncio
async def test_send_checkin_can_be_called_manually() -> None:
    with patch("app.scheduler.jobs.send_notification", new=AsyncMock(return_value=False)):
        await send_checkin("morning")


@pytest.mark.asyncio
async def test_embeddings_stub_job() -> None:
    await process_pending_embeddings_stub()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_due_reminders_job(db_session, default_user_id) -> None:
    service = ReminderService(db_session)
    reminder = await service.create(
        default_user_id,
        ReminderCreate(
            title="Lembrete vencido",
            remind_at=datetime.now(timezone.utc),
        ),
    )
    await db_session.flush()

    class MockSessionLocal:
        def __call__(self):
            return self._ctx()

        @asynccontextmanager
        async def _ctx(self):
            yield db_session

    with patch("app.scheduler.jobs.AsyncSessionLocal", MockSessionLocal()):
        with patch("app.scheduler.jobs.send_notification", new=AsyncMock(return_value=False)):
            await process_due_reminders()

    updated = await service.repo.get_by_id(reminder.id, default_user_id)
    assert updated is not None
    assert updated.status.value == "sent"


@pytest.mark.asyncio
async def test_send_daily_summary_job_manual() -> None:
    class MockSessionLocal:
        def __call__(self):
            return self._ctx()

        @asynccontextmanager
        async def _ctx(self):
            yield AsyncMock()

    with patch("app.scheduler.jobs.AsyncSessionLocal", MockSessionLocal()):
        with patch(
            "app.scheduler.jobs.build_daily_summary",
            new=AsyncMock(return_value="Resumo teste"),
        ):
            with patch("app.scheduler.jobs.send_notification", new=AsyncMock(return_value=False)):
                await send_daily_summary_job()
