"""Tests for Telegram command handlers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.telegram.commands import cmd_help, cmd_start


@pytest.mark.asyncio
async def test_cmd_start_unauthorized() -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=99999)
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.commands.is_user_allowed", return_value=False):
        await cmd_start(update, context)

    update.message.reply_text.assert_awaited_once()
    assert "não autorizado" in update.message.reply_text.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_cmd_start_returns_welcome() -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.commands.is_user_allowed", return_value=True):
        await cmd_start(update, context)

    reply = update.message.reply_text.await_args.args[0]
    assert "Copiloto" in reply
    assert "conversar" in reply.lower()


@pytest.mark.asyncio
async def test_cmd_help_returns_examples() -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.commands.is_user_allowed", return_value=True):
        await cmd_help(update, context)

    reply = update.message.reply_text.await_args.args[0]
    assert "Estudei Python" in reply
    assert "Medicina" in reply
