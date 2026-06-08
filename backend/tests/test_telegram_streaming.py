"""Tests for Telegram streaming."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.brain.schemas import BrainResult
from app.brain.telegram_streamer import stream_telegram_response


@pytest.mark.asyncio
async def test_streaming_edits_in_blocks() -> None:
    message = MagicMock()
    sent = MagicMock()
    sent.edit_text = AsyncMock()
    message.reply_text = AsyncMock(return_value=sent)

    long_response = "A" * 400

    async def factory():
        return BrainResult(
            response=long_response,
            used_fallback=True,
            response_time_ms=10,
        )

    with patch("app.brain.telegram_streamer.get_settings") as mock_settings:
        mock_settings.return_value.telegram_streaming_enabled = True
        mock_settings.return_value.telegram_stream_edit_interval_ms = 100
        mock_settings.return_value.telegram_stream_min_chars = 50
        result = await stream_telegram_response(message, factory)

    assert result.response == long_response
    assert sent.edit_text.await_count >= 1
    message.reply_text.assert_awaited_once()
