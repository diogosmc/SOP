"""Tests for Telegram Jarvis Instructor pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.finance.models import FinanceTransaction
from app.modules.notes.models import Note
from app.modules.tasks.models import Task
from app.telegram.commands import cmd_debug
from app.telegram.handlers import handle_free_text
from app.telegram.instructor import classify_telegram_message, process_telegram_message


class _SessionContext:
    def __init__(self, session) -> None:
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.asyncio
async def test_classify_autoescola_as_appointment() -> None:
    result = classify_telegram_message("Amanha eu vou ter auto escola")
    assert result["intent"] == "appointment"
    assert result["entities"]["title"].lower() == "autoescola"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_autoescola_message_does_not_break(db_session, default_user_id) -> None:
    with patch("app.telegram.instructor._try_llm_reply", new=AsyncMock(return_value=None)):
        reply = await process_telegram_message(
            db_session, default_user_id, "Amanha eu vou ter auto escola", skip_llm=True
        )

    assert "algo deu errado" not in reply.lower()
    assert "autoescola" in reply.lower() or "anotei" in reply.lower()

    tasks = list(
        (await db_session.execute(select(Task).where(Task.user_id == default_user_id))).scalars()
    )
    assert any("autoescola" in t.title.lower() for t in tasks)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_desanimado_message_does_not_break(db_session, default_user_id) -> None:
    reply = await process_telegram_message(
        db_session, default_user_id, "Estou desanimado hoje", skip_llm=True
    )

    assert "algo deu errado" not in reply.lower()
    assert "entendi" in reply.lower() or "simplificar" in reply.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_study_revision_creates_task_or_fallback(db_session, default_user_id) -> None:
    reply = await process_telegram_message(
        db_session,
        default_user_id,
        "Preciso revisar anatomia amanhã",
        skip_llm=True,
    )

    assert "algo deu errado" not in reply.lower()
    tasks = list(
        (await db_session.execute(select(Task).where(Task.user_id == default_user_id))).scalars()
    )
    assert tasks or "estudo" in reply.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expense_registers_finance_or_fallback(db_session, default_user_id) -> None:
    reply = await process_telegram_message(
        db_session, default_user_id, "Gastei 20 no lanche", skip_llm=True
    )

    assert "algo deu errado" not in reply.lower()
    txs = list(
        (
            await db_session.execute(
                select(FinanceTransaction).where(FinanceTransaction.user_id == default_user_id)
            )
        ).scalars()
    )
    assert txs or "gasto" in reply.lower() or "registrei" in reply.lower()


@pytest.mark.asyncio
async def test_ollama_offline_does_not_break_telegram(db_session, default_user_id) -> None:
    with patch("app.telegram.instructor.check_ollama_health", new=AsyncMock(return_value=False)):
        reply = await process_telegram_message(
            db_session, default_user_id, "Como organizar meu dia?", skip_llm=False
        )

    assert reply
    assert "algo deu errado" not in reply.lower()


@pytest.mark.asyncio
async def test_memory_failure_does_not_break_telegram(db_session, default_user_id) -> None:
    with patch(
        "app.telegram.instructor.update_daily_journal_from_message",
        side_effect=RuntimeError("journal failed"),
    ):
        reply = await process_telegram_message(
            db_session, default_user_id, "Estou desanimado hoje", skip_llm=True
        )

    assert reply
    assert "algo deu errado" not in reply.lower()


@pytest.mark.asyncio
async def test_integrity_error_handler_still_replies(db_session) -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.text = "Amanha eu vou ter auto escola"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.handlers.is_user_allowed", return_value=True):
        with patch(
            "app.telegram.handlers.AsyncSessionLocal",
            return_value=_SessionContext(db_session),
        ):
            with patch(
                "app.telegram.handlers.process_telegram_message",
                side_effect=IntegrityError("fk", {}, Exception("fk")),
            ):
                await handle_free_text(update, context)

    reply_text = update.message.reply_text.await_args.args[0].lower()
    assert "algo deu errado" not in reply_text
    assert "usuário padrão" in reply_text or "default" in reply_text or "padrão" in reply_text


@pytest.mark.asyncio
async def test_note_creation_from_anota_que(db_session, default_user_id) -> None:
    reply = await process_telegram_message(
        db_session,
        default_user_id,
        "Anota que segunda eu preciso resolver pendências",
        skip_llm=True,
    )

    assert "algo deu errado" not in reply.lower()
    notes = list(
        (await db_session.execute(select(Note).where(Note.user_id == default_user_id))).scalars()
    )
    assert notes or "anotado" in reply.lower() or "contexto" in reply.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cmd_debug_returns_status(db_session, default_user_id) -> None:
    update = MagicMock()
    update.effective_user = MagicMock(id=12345)
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("app.telegram.commands.is_user_allowed", return_value=True):
        with patch("app.telegram.commands.check_database_health", new=AsyncMock(return_value=True)):
            with patch("app.telegram.commands.check_redis_health", new=AsyncMock(return_value=True)):
                with patch("app.telegram.commands.check_ollama_health", new=AsyncMock(return_value=False)):
                    with patch(
                        "app.telegram.commands.AsyncSessionLocal",
                        return_value=_SessionContext(db_session),
                    ):
                        await cmd_debug(update, context)

    reply = update.message.reply_text.await_args.args[0]
    assert "Debug" in reply
    assert "DB:" in reply
    assert "Ollama:" in reply
    assert "Default user:" in reply
