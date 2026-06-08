"""AI tool handlers for Telegram intents."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.classifier import ClassificationResult
from app.ai.ollama import OllamaClient
from app.ai.prompts.system import SYSTEM_PROMPT
from app.core.config import get_settings
from app.modules.finance.service import FinanceService
from app.modules.habits.models import Habit
from app.modules.habits.schemas import HabitLogCreate
from app.modules.habits.service import HabitService
from app.modules.study.service import StudyService
from app.modules.tasks.schemas import TaskCreate
from app.modules.tasks.service import TaskService
from app.modules.workout.service import WorkoutService


async def handle_expense_log(
    db: AsyncSession, user_id: uuid.UUID, classification: ClassificationResult
) -> str:
    entities = classification.entities
    amount = entities.get("amount")
    if amount is None:
        return "Não identifiquei o valor. Ex.: Gastei 30 reais no almoço."

    service = FinanceService(db)
    await service.log_expense(
        user_id,
        amount=Decimal(str(amount)),
        description=entities.get("description") or entities.get("raw_message"),
        category_name=entities.get("category"),
    )
    return f"Despesa de R${Decimal(str(amount)):.2f} registrada."


async def handle_habit_log(
    db: AsyncSession, user_id: uuid.UUID, classification: ClassificationResult
) -> str:
    entities = classification.entities
    habit_name = entities.get("habit_name")

    query = select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True))
    if habit_name:
        query = query.where(Habit.name.ilike(f"%{habit_name}%"))
    query = query.order_by(Habit.created_at.asc()).limit(1)

    result = await db.execute(query)
    habit = result.scalar_one_or_none()
    if not habit:
        return "Nenhum hábito ativo encontrado. Crie um hábito no dashboard primeiro."

    service = HabitService(db)
    await service.log_habit(
        habit.id,
        user_id,
        HabitLogCreate(
            completed=True,
            notes=entities.get("notes") or entities.get("raw_message"),
        ),
    )
    return f"Hábito '{habit.name}' marcado como feito."


async def handle_task_creation(
    db: AsyncSession, user_id: uuid.UUID, classification: ClassificationResult
) -> str:
    entities = classification.entities
    title = entities.get("title") or entities.get("raw_message")
    if not title:
        return "Qual tarefa devo criar?"

    service = TaskService(db)
    task = await service.create(user_id, TaskCreate(title=str(title)[:500]))
    return f"Tarefa criada: {task.title}"


async def handle_study_log(
    db: AsyncSession, user_id: uuid.UUID, classification: ClassificationResult
) -> str:
    entities = classification.entities
    duration = entities.get("duration_minutes", 30)
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 30

    from app.modules.study.schemas import StudySessionCreate

    service = StudyService(db)
    session = await service.log_session(
        user_id,
        StudySessionCreate(
            duration_minutes=duration,
            notes=entities.get("notes") or entities.get("raw_message"),
        ),
    )
    return f"Sessão de estudo registrada ({session.duration_minutes} min)."


async def handle_workout_log(
    db: AsyncSession, user_id: uuid.UUID, classification: ClassificationResult
) -> str:
    entities = classification.entities
    duration = entities.get("duration_minutes")
    if duration is not None:
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            duration = None

    from app.modules.workout.schemas import SessionCreate

    service = WorkoutService(db)
    session = await service.create_session(
        user_id,
        SessionCreate(
            session_date=date.today(),
            notes=entities.get("notes") or entities.get("raw_message"),
            duration_minutes=duration,
        ),
    )
    return f"Treino registrado{ f' ({session.duration_minutes} min)' if session.duration_minutes else ''}."


async def handle_general_chat(
    db: AsyncSession,
    user_id: uuid.UUID,
    classification: ClassificationResult,
    *,
    ollama: OllamaClient | None = None,
) -> str:
    _ = db, user_id, classification
    client = ollama or OllamaClient()
    settings = get_settings()
    message = str(classification.entities.get("raw_message", ""))

    result = await client.chat(
        settings.ollama_main_model,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        options={"temperature": 0.7},
    )
    content = result.get("message", {})
    if isinstance(content, dict):
        text = content.get("content", "")
        if isinstance(text, str) and text.strip():
            return text.strip()

    response = result.get("response")
    if isinstance(response, str) and response.strip():
        return response.strip()

    return "Entendi. Como posso ajudar?"
