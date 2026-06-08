"""Daily and weekly summary builders."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.memory.models import AIMemory, DailyJournal
from app.modules.memory.repository import MemoryRepository
from app.modules.tasks.models import Task, TaskStatus


def _local_today() -> datetime.date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


async def build_daily_summary(user_id: uuid.UUID, db: AsyncSession) -> str:
    """Build a text summary from today's journal and basic stats."""
    today = _local_today()
    repo = MemoryRepository(db)
    journal = await repo.get_journal_by_date(user_id, today)

    parts: list[str] = [f"Resumo de {today.strftime('%d/%m/%Y')}:"]

    if journal:
        if journal.summary:
            parts.append(f"Geral: {journal.summary}")
        if journal.mood_score is not None:
            parts.append(f"Humor: {journal.mood_score}/10")
        if journal.study_summary:
            parts.append(f"Estudos: {journal.study_summary}")
        if journal.workout_summary:
            parts.append(f"Treino: {journal.workout_summary}")
        if journal.finance_summary:
            parts.append(f"Finanças: {journal.finance_summary}")
        if journal.habit_summary:
            parts.append(f"Hábitos: {journal.habit_summary}")
    else:
        parts.append("Nenhum registro no diário hoje.")

    pending_result = await db.execute(
        select(Task)
        .where(Task.user_id == user_id, Task.status == TaskStatus.PENDING)
        .limit(5)
    )
    pending_tasks = list(pending_result.scalars().all())
    if pending_tasks:
        titles = ", ".join(task.title for task in pending_tasks)
        parts.append(f"Tarefas pendentes: {titles}")

    return "\n\n".join(parts)


async def build_weekly_summary(user_id: uuid.UUID, db: AsyncSession) -> str:
    """Build a basic weekly summary from journals and memories."""
    today = _local_today()
    week_start = today - timedelta(days=6)

    journals_result = await db.execute(
        select(DailyJournal)
        .where(
            DailyJournal.user_id == user_id,
            DailyJournal.date >= week_start,
            DailyJournal.date <= today,
        )
        .order_by(DailyJournal.date.asc())
    )
    journals = list(journals_result.scalars().all())

    memories_result = await db.execute(
        select(AIMemory)
        .where(AIMemory.user_id == user_id)
        .order_by(AIMemory.updated_at.desc())
        .limit(5)
    )
    memories = list(memories_result.scalars().all())

    parts: list[str] = [
        f"Revisão semanal ({week_start.strftime('%d/%m')} — {today.strftime('%d/%m')}):"
    ]

    if journals:
        parts.append(f"Dias com registros no diário: {len(journals)}")
        study_days = sum(1 for j in journals if j.study_summary)
        workout_days = sum(1 for j in journals if j.workout_summary)
        if study_days:
            parts.append(f"Dias com estudo registrado: {study_days}")
        if workout_days:
            parts.append(f"Dias com treino registrado: {workout_days}")
    else:
        parts.append("Poucos registros no diário esta semana.")

    if memories:
        highlights = "; ".join(memory.content[:80] for memory in memories[:3])
        parts.append(f"Memórias recentes: {highlights}")

    parts.append("Continue consistente na próxima semana.")
    return "\n\n".join(parts)
