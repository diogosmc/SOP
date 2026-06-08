"""Daily and weekly summary jobs."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.modules.finance.models import FinanceTransaction, TransactionType
from app.modules.habits.models import HabitLog
from app.modules.memory.models import DailyJournal, WeeklyReview
from app.modules.study.models import StudySession
from app.modules.tasks.models import Task, TaskStatus
from app.modules.workout.models import WorkoutSession
from app.telegram.bot import send_telegram_message

logger = get_logger(__name__)


async def _collect_day_stats(db: AsyncSession, user_id: uuid.UUID, day: date) -> dict[str, str]:
    study_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
            StudySession.user_id == user_id,
            func.date(StudySession.created_at) == day,
        )
    )
    study_minutes = int(study_result.scalar_one())

    workout_result = await db.execute(
        select(func.count()).select_from(WorkoutSession).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date == day,
        )
    )
    workout_count = int(workout_result.scalar_one())

    expense_result = await db.execute(
        select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
            FinanceTransaction.user_id == user_id,
            FinanceTransaction.transaction_type == TransactionType.EXPENSE,
            FinanceTransaction.transaction_date == day,
        )
    )
    expenses = expense_result.scalar_one()

    habit_result = await db.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.log_date == day,
            HabitLog.completed.is_(True),
        )
    )
    habits_done = int(habit_result.scalar_one())

    tasks_result = await db.execute(
        select(func.count()).select_from(Task).where(
            Task.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
            func.date(Task.completed_at) == day,
        )
    )
    tasks_done = int(tasks_result.scalar_one())

    return {
        "study": f"{study_minutes // 60}h{study_minutes % 60:02d} de estudo" if study_minutes else "sem estudo",
        "workout": f"{workout_count} treino(s)" if workout_count else "sem treino",
        "finance": f"R${expenses:.2f} em despesas",
        "habits": f"{habits_done} hábito(s) concluído(s)",
        "tasks": f"{tasks_done} tarefa(s) concluída(s)",
    }


async def _generate_summary(prompt: str) -> str:
    settings = get_settings()
    client = OllamaClient()
    try:
        result = await client.generate(
            settings.ollama_main_model,
            prompt,
            options={"temperature": 0.4},
        )
        text = str(result.get("response", "")).strip()
        if text:
            return text[:2000]
    except Exception as exc:
        logger.warning("summary_generation_failed", error=str(exc))
    return "Resumo indisponível no momento."


async def send_daily_summary() -> None:
    """Generate and send the daily journal at 23:00."""
    settings = get_settings()
    if not settings.telegram_enabled:
        return

    user_id = uuid.UUID(settings.default_user_id)
    today = date.today()

    async with AsyncSessionLocal() as db:
        stats = await _collect_day_stats(db, user_id, today)
        prompt = (
            "Gere um resumo diário curto (até 3 parágrafos) em português:\n"
            f"- {stats['study']}\n"
            f"- {stats['workout']}\n"
            f"- {stats['finance']}\n"
            f"- {stats['habits']}\n"
            f"- {stats['tasks']}"
        )
        summary = await _generate_summary(prompt)

        journal = DailyJournal(
            user_id=user_id,
            date=datetime.now(timezone.utc),
            summary=summary,
            study_summary=stats["study"],
            workout_summary=stats["workout"],
            finance_summary=stats["finance"],
            habit_summary=stats["habits"],
        )
        db.add(journal)
        await db.commit()

    sent = await send_telegram_message(f"Resumo do dia:\n\n{summary}")
    if sent:
        logger.info("daily_summary_sent")


async def send_weekly_summary() -> None:
    """Generate and send the weekly review on Sunday at 20:00."""
    settings = get_settings()
    if not settings.telegram_enabled:
        return

    user_id = uuid.UUID(settings.default_user_id)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_ref = f"{week_start.isocalendar().year}-W{week_start.isocalendar().week:02d}"

    async with AsyncSessionLocal() as db:
        study_result = await db.execute(
            select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
                StudySession.user_id == user_id,
                func.date(StudySession.created_at) >= week_start,
            )
        )
        study_hours = int(study_result.scalar_one()) / 60

        workout_result = await db.execute(
            select(func.count()).select_from(WorkoutSession).where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.session_date >= week_start,
            )
        )
        workouts = int(workout_result.scalar_one())

        prompt = (
            "Gere uma revisão semanal curta (até 4 parágrafos) em português:\n"
            f"- {study_hours:.1f} horas de estudo\n"
            f"- {workouts} treinos\n"
            "Inclua vitórias, pontos a melhorar e uma recomendação."
        )
        summary = await _generate_summary(prompt)

        review = WeeklyReview(
            user_id=user_id,
            week_reference=week_ref,
            summary=summary,
        )
        db.add(review)
        await db.commit()

    sent = await send_telegram_message(f"Revisão semanal:\n\n{summary}")
    if sent:
        logger.info("weekly_summary_sent")
