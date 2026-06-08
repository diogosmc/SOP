"""Execute Brain actions using existing services."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.journal import update_daily_journal_from_message
from app.brain.schemas import BrainAction
from app.modules.finance.models import TransactionType
from app.modules.finance.schemas import TransactionCreate
from app.modules.finance.service import FinanceService
from app.modules.memory.models import MemoryType
from app.modules.memory.repository import MemoryRepository
from app.modules.notes.schemas import NoteCreate
from app.modules.notes.service import NoteService
from app.modules.reminders.schemas import ReminderCreate
from app.modules.reminders.service import ReminderService
from app.modules.tasks.schemas import TaskCreate
from app.modules.tasks.service import TaskService
from app.brain.utils import coerce_datetime, extract_expense_details, local_today

logger = logging.getLogger(__name__)


async def _rollback_safe(db: AsyncSession) -> None:
    try:
        await db.rollback()
    except Exception:
        pass


async def execute_actions(
    db: AsyncSession,
    user_id: uuid.UUID,
    actions: list[BrainAction],
    classification: dict[str, Any],
) -> list[BrainAction]:
    results: list[BrainAction] = []
    for action in actions:
        if action.action == "none":
            results.append(action)
            continue
        try:
            await _execute_one(db, user_id, action, classification)
            action.success = True
        except Exception as exc:
            await _rollback_safe(db)
            action.success = False
            action.error = str(exc)
            logger.exception("brain_action_failed action=%s user_id=%s", action.action, user_id)
        results.append(action)
    return results


async def _execute_one(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: BrainAction,
    classification: dict[str, Any],
) -> None:
    params = action.params

    if action.action == "create_task":
        title = str(params.get("title", "")).strip()
        if not title:
            return
        await TaskService(db).create(
            user_id,
            TaskCreate(
                title=title[:500],
                due_date=coerce_datetime(params.get("due_date")),
                category=params.get("category"),
            ),
        )

    elif action.action == "create_reminder":
        title = str(params.get("title", "Lembrete")).strip()
        remind_at = coerce_datetime(params.get("remind_at"))
        if not remind_at:
            return
        await ReminderService(db).create(
            user_id,
            ReminderCreate(title=title[:500], remind_at=remind_at),
        )

    elif action.action == "create_note":
        await NoteService(db).create(
            user_id,
            NoteCreate(
                title=str(params.get("title", "Nota"))[:500],
                content=str(params.get("content", "")),
                tags=["telegram", "brain"],
            ),
        )

    elif action.action == "create_memory":
        repo = MemoryRepository(db)
        memory_type_raw = params.get("memory_type", "other")
        try:
            memory_type = MemoryType(memory_type_raw)
        except ValueError:
            memory_type = MemoryType.OTHER
        await repo.create(
            user_id,
            memory_type=memory_type,
            content=str(params.get("content", ""))[:2000],
            importance=int(params.get("importance", 5)),
            confidence=float(params.get("confidence", 0.7)),
            source="telegram_brain",
        )

    elif action.action == "update_journal":
        await update_daily_journal_from_message(
            user_id,
            str(params.get("message", "")),
            classification,
            db,
        )

    elif action.action == "create_finance_transaction":
        message = str(params.get("message", ""))
        entities = params.get("entities") or {}
        amount, category, description = extract_expense_details(message, entities)
        if amount <= 0:
            return
        await FinanceService(db).create(
            user_id,
            TransactionCreate(
                description=description,
                amount=amount,
                type=TransactionType.EXPENSE,
                category=category,
                transaction_date=local_today(),
            ),
        )

    elif action.action == "create_study_log":
        title = "Registro de estudo"
        message = str(params.get("message", ""))
        if "python" in message.lower():
            title = "Estudo: Python"
        await NoteService(db).create(
            user_id,
            NoteCreate(title=title, content=message, tags=["estudo", "telegram"]),
        )

    elif action.action == "create_workout_log":
        await update_daily_journal_from_message(
            user_id,
            str(params.get("message", "")),
            {**classification, "intent": "workout_log"},
            db,
        )
