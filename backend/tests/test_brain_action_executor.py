"""Tests for brain action executor."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.brain.action_executor import execute_actions
from app.brain.schemas import BrainAction
from app.modules.finance.models import FinanceTransaction
from app.modules.notes.models import Note
from app.modules.tasks.models import Task
from app.telegram.instructor import classify_telegram_message


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expense_action_creates_transaction(db_session, default_user_id) -> None:
    message = "Gastei 20 no lanche"
    classification = classify_telegram_message(message)
    actions = [
        BrainAction(
            action="create_finance_transaction",
            params={"message": message, "entities": classification["entities"]},
        )
    ]
    results = await execute_actions(db_session, default_user_id, actions, classification)
    assert results[0].success
    txs = list(
        (
            await db_session.execute(
                select(FinanceTransaction).where(FinanceTransaction.user_id == default_user_id)
            )
        ).scalars()
    )
    assert txs


@pytest.mark.integration
@pytest.mark.asyncio
async def test_note_action_creates_note(db_session, default_user_id) -> None:
    message = "Anota que segunda eu preciso resolver pendências"
    classification = classify_telegram_message(message)
    entities = classification["entities"]
    actions = [
        BrainAction(
            action="create_note",
            params={"title": entities["title"], "content": entities["content"]},
        )
    ]
    results = await execute_actions(db_session, default_user_id, actions, classification)
    assert results[0].success
    notes = list(
        (await db_session.execute(select(Note).where(Note.user_id == default_user_id))).scalars()
    )
    assert notes


@pytest.mark.asyncio
async def test_action_failure_does_not_break(db_session, default_user_id) -> None:
    classification = classify_telegram_message("teste")
    actions = [BrainAction(action="create_task", params={"title": "Tarefa teste"})]
    with patch(
        "app.brain.action_executor.TaskService.create",
        new=AsyncMock(side_effect=RuntimeError("fail")),
    ):
        results = await execute_actions(db_session, default_user_id, actions, classification)
    assert results[0].success is False
    assert results[0].error
