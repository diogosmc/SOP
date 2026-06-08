"""Integration tests for Telegram + Conversation Brain."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.brain.conversation_manager import process_message
from app.telegram.handlers import handle_free_text


class _SessionContext:
    def __init__(self, session) -> None:
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_brain_emotional_message(db_session, default_user_id) -> None:
    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=False)):
        result = await process_message(
            db_session, default_user_id, "Estou desanimado hoje", allow_llm=False
        )
    assert "algo deu errado" not in result.response.lower()
    assert result.intent == "emotional_checkin"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_brain_ack_short(db_session, default_user_id) -> None:
    result = await process_message(db_session, default_user_id, "Não vlw", allow_llm=False)
    assert len(result.response) <= 20


@pytest.mark.asyncio
async def test_handler_never_returns_generic_error(db_session) -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.text = "Amanhã tenho autoescola às 8"
    update.message.reply_text = AsyncMock()
    sent = MagicMock()
    sent.edit_text = AsyncMock()
    update.message.reply_text.return_value = sent
    context = MagicMock()

    with patch("app.telegram.handlers.AsyncSessionLocal", return_value=_SessionContext(db_session)):
        with patch("app.telegram.handlers.is_user_allowed", return_value=True):
            with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=False)):
                await handle_free_text(update, context)

    calls = update.message.reply_text.await_args_list + sent.edit_text.await_args_list
    assert calls
    for call in calls:
        text = call.args[0].lower()
        assert "algo deu errado" not in text


@pytest.mark.asyncio
async def test_memory_failure_does_not_break_brain(db_session, default_user_id) -> None:
    with patch(
        "app.brain.action_executor.update_daily_journal_from_message",
        side_effect=RuntimeError("journal fail"),
    ):
        with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=False)):
            result = await process_message(
                db_session, default_user_id, "Estou desanimado hoje", allow_llm=False
            )
    assert result.response
    assert "algo deu errado" not in result.response.lower()
