"""Tests for Telegram security and bot lifecycle."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.telegram.bot import TelegramBot, reset_telegram_bot, start_telegram_bot
from app.telegram.security import is_user_allowed, should_start_bot


@pytest.fixture(autouse=True)
def _reset_bot_singleton() -> None:
    reset_telegram_bot()
    yield
    reset_telegram_bot()


def test_should_start_bot_disabled() -> None:
    settings = Settings(telegram_enabled=False, telegram_bot_token="token")
    assert should_start_bot(settings) is False


def test_should_start_bot_missing_token() -> None:
    settings = Settings(telegram_enabled=True, telegram_bot_token="")
    assert should_start_bot(settings) is False


def test_should_start_bot_enabled_with_token() -> None:
    settings = Settings(
        telegram_enabled=True,
        telegram_bot_token="abc123",
        telegram_allowed_user_id="123456789",
    )
    assert should_start_bot(settings) is True


def test_should_start_bot_invalid_user_id_placeholder() -> None:
    settings = Settings(
        telegram_enabled=True,
        telegram_bot_token="abc123",
        telegram_allowed_user_id="SEU_ID",
    )
    assert should_start_bot(settings) is False


def test_unauthorized_user_blocked() -> None:
    settings = Settings(telegram_allowed_user_id="12345")
    assert is_user_allowed(99999, settings) is False
    assert is_user_allowed(12345, settings) is True


@pytest.mark.asyncio
async def test_start_telegram_bot_disabled_does_not_start() -> None:
    with patch("app.telegram.bot.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            telegram_enabled=False,
            telegram_bot_token="token",
        )
        started = await start_telegram_bot()
    assert started is False


@pytest.mark.asyncio
async def test_telegram_start_failure_does_not_raise() -> None:
    def bad_builder(_token: str) -> MagicMock:
        raise RuntimeError("boom")

    bot = TelegramBot(application_builder=bad_builder)

    with patch("app.telegram.bot.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            telegram_enabled=True,
            telegram_bot_token="token",
        )
        started = await bot.start()

    assert started is False
    assert bot.is_running is False


@pytest.mark.asyncio
async def test_telegram_stop_handles_errors() -> None:
    bot = TelegramBot()
    bot.application = MagicMock()
    bot.application.updater.stop = AsyncMock(side_effect=RuntimeError("stop failed"))
    bot.application.stop = AsyncMock()
    bot.application.shutdown = AsyncMock()
    bot._running = True

    await bot.stop()
    assert bot.is_running is False
