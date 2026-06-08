"""Tests for Telegram Instructor message routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.modules.memory.models import AIMemory, MemoryType
from app.modules.notes.models import Note
from app.telegram.handlers import handle_free_text
from app.telegram.tools import route_instructor_message


@pytest.mark.integration
@pytest.mark.asyncio
async def test_route_instructor_calls_classifier(db_session, default_user_id) -> None:
    mock_classify = MagicMock(
        return_value={
            "intent": "general_chat",
            "categories": [],
            "entities": {},
            "should_save_memory": False,
            "should_create_note": False,
            "requires_confirmation": False,
        }
    )
    mock_chat = AsyncMock(
        return_value=MagicMock(response="Resposta mockada", model_used="test", response_time_ms=1)
    )

    with patch("app.telegram.tools.handle_chat_fallback", new=AsyncMock(return_value="Resposta mockada")):
        reply = await route_instructor_message(
            db_session,
            default_user_id,
            "Como organizar meu dia?",
            classify_func=mock_classify,
        )

    mock_classify.assert_called_once()
    assert reply == "Resposta mockada"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_route_instructor_medicina_creates_memory(db_session, default_user_id) -> None:
    reply = await route_instructor_message(
        db_session, default_user_id, "Quero passar em Medicina"
    )

    result = await db_session.execute(
        select(AIMemory).where(
            AIMemory.user_id == default_user_id,
            AIMemory.type == MemoryType.GOAL,
        )
    )
    memories = list(result.scalars().all())
    assert memories
    assert "medicina" in memories[0].content.lower()
    assert "memória" in reply.lower() or "objetivo" in reply.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_route_instructor_study_creates_note_and_journal(
    db_session, default_user_id
) -> None:
    reply = await route_instructor_message(db_session, default_user_id, "Estudei Python")

    notes_result = await db_session.execute(
        select(Note).where(Note.user_id == default_user_id)
    )
    notes = list(notes_result.scalars().all())
    assert notes
    assert any("python" in note.title.lower() or "python" in note.content.lower() for note in notes)
    assert "estudo" in reply.lower() or "anotado" in reply.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_route_instructor_chat_fallback_mocked(db_session, default_user_id) -> None:
    mock_fallback = AsyncMock(return_value="Fallback IA")

    with patch("app.telegram.tools.handle_chat_fallback", mock_fallback):
        reply = await route_instructor_message(
            db_session,
            default_user_id,
            "Me explique loops em Python",
            classify_func=lambda _text: {
                "intent": "question",
                "categories": [],
                "entities": {},
                "should_save_memory": False,
                "should_create_note": False,
                "requires_confirmation": False,
            },
        )

    assert reply == "Fallback IA"
    mock_fallback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_free_text_unauthorized() -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=99999)
    update.message = MagicMock()
    update.message.text = "Quero passar em Medicina"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.handlers.is_user_allowed", return_value=False):
        await handle_free_text(update, context)

    update.message.reply_text.assert_awaited_once_with("Acesso não autorizado.")


@pytest.mark.asyncio
async def test_import_app_with_telegram_lifecycle() -> None:
    with patch("app.main.start_telegram_bot", new=AsyncMock(return_value=False)):
        with patch("app.main.stop_telegram_bot", new=AsyncMock()):
            from app.main import app

            assert app.title == "COPILOTO"
