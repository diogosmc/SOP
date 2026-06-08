"""Tests for APScheduler setup."""

from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.scheduler.app import (
    configure_scheduler,
    reset_scheduler,
    should_start_scheduler,
    start_scheduler,
)


@pytest.fixture(autouse=True)
def _clean_scheduler() -> None:
    reset_scheduler()
    yield
    reset_scheduler()


def test_scheduler_disabled_does_not_start() -> None:
    settings = Settings(scheduler_enabled=False)
    assert should_start_scheduler(settings) is False
    assert configure_scheduler(settings) == 0


@pytest.mark.asyncio
async def test_start_scheduler_disabled() -> None:
    with patch("app.scheduler.app.get_settings") as mock_settings:
        mock_settings.return_value = Settings(scheduler_enabled=False)
        started = await start_scheduler()
    assert started is False


@pytest.mark.asyncio
async def test_scheduler_enabled_registers_jobs() -> None:
    settings = Settings(scheduler_enabled=True)
    count = configure_scheduler(settings)
    assert count == 8
    job_ids = {job.id for job in __import__("app.scheduler.app", fromlist=["scheduler"]).scheduler.get_jobs()}
    assert job_ids == {
        "process_due_reminders",
        "checkin_morning",
        "checkin_noon",
        "checkin_evening",
        "checkin_night",
        "daily_summary",
        "weekly_summary",
        "embeddings_stub",
    }


@pytest.mark.asyncio
async def test_scheduler_start_failure_does_not_raise() -> None:
    with patch("app.scheduler.app.get_settings") as mock_settings:
        mock_settings.return_value = Settings(scheduler_enabled=True)
        with patch("app.scheduler.app.scheduler.start", side_effect=RuntimeError("boom")):
            started = await start_scheduler()
    assert started is False
