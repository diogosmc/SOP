"""Cross-module pattern detection and insight generation."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient, OllamaError
from app.ai.router import select_model
from app.modules.finance.models import FinanceTransaction, TransactionType
from app.modules.habits.models import Habit, HabitLog
from app.modules.study.models import StudySession, StudyTopic, TopicStatus
from app.modules.tasks.models import Task, TaskStatus
from app.modules.workout.models import WorkoutSession


def _extract_ollama_content(response: dict[str, Any]) -> str:
    message = response.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
    response_text = response.get("response")
    if isinstance(response_text, str):
        return response_text
    return ""


async def _collect_module_stats(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    income_result = await db.execute(
        select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
            FinanceTransaction.user_id == user_id,
            FinanceTransaction.transaction_type == TransactionType.INCOME,
            FinanceTransaction.transaction_date >= week_start,
            FinanceTransaction.transaction_date <= week_end,
        )
    )
    expense_result = await db.execute(
        select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
            FinanceTransaction.user_id == user_id,
            FinanceTransaction.transaction_type == TransactionType.EXPENSE,
            FinanceTransaction.transaction_date >= week_start,
            FinanceTransaction.transaction_date <= week_end,
        )
    )

    study_minutes_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
            StudySession.user_id == user_id,
            StudySession.created_at >= datetime.combine(week_start, datetime.min.time()).replace(
                tzinfo=timezone.utc
            ),
        )
    )
    topics_in_progress_result = await db.execute(
        select(func.count())
        .select_from(StudyTopic)
        .where(StudyTopic.user_id == user_id, StudyTopic.status == TopicStatus.IN_PROGRESS)
    )

    workout_sessions_result = await db.execute(
        select(func.count())
        .select_from(WorkoutSession)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= week_start,
            WorkoutSession.session_date <= week_end,
        )
    )

    tasks_completed_result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
    )
    tasks_pending_result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        )
    )

    active_habits_result = await db.execute(
        select(func.count()).select_from(Habit).where(Habit.user_id == user_id, Habit.is_active)
    )
    habit_logs_result = await db.execute(
        select(func.count())
        .select_from(HabitLog)
        .join(Habit, HabitLog.habit_id == Habit.id)
        .where(
            Habit.user_id == user_id,
            HabitLog.log_date >= week_start,
            HabitLog.log_date <= week_end,
            HabitLog.completed.is_(True),
        )
    )

    income = Decimal(str(income_result.scalar_one()))
    expense = Decimal(str(expense_result.scalar_one()))

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "finance": {
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense),
            "savings_rate": float((income - expense) / income * 100) if income > 0 else 0.0,
        },
        "study": {
            "minutes_this_week": int(study_minutes_result.scalar_one()),
            "topics_in_progress": int(topics_in_progress_result.scalar_one()),
        },
        "workout": {
            "sessions_this_week": int(workout_sessions_result.scalar_one()),
        },
        "tasks": {
            "completed": int(tasks_completed_result.scalar_one()),
            "pending": int(tasks_pending_result.scalar_one()),
        },
        "habits": {
            "active": int(active_habits_result.scalar_one()),
            "completions_this_week": int(habit_logs_result.scalar_one()),
        },
    }


def _detect_patterns(stats: dict[str, Any]) -> list[dict[str, str]]:
    patterns: list[dict[str, str]] = []

    finance = stats["finance"]
    if finance["expense"] > finance["income"] and finance["income"] > 0:
        patterns.append(
            {
                "type": "financial",
                "pattern": "spending_exceeds_income",
                "description": "Weekly expenses exceed income.",
            }
        )
    elif finance["savings_rate"] >= 20:
        patterns.append(
            {
                "type": "financial",
                "pattern": "healthy_savings",
                "description": f"Savings rate is {finance['savings_rate']:.0f}%.",
            }
        )

    study = stats["study"]
    if study["minutes_this_week"] < 60 and study["topics_in_progress"] > 0:
        patterns.append(
            {
                "type": "study",
                "pattern": "low_study_time",
                "description": "Less than 1 hour of study this week with topics in progress.",
            }
        )
    elif study["minutes_this_week"] >= 300:
        patterns.append(
            {
                "type": "study",
                "pattern": "consistent_study",
                "description": "Strong study consistency this week (5+ hours).",
            }
        )

    workout = stats["workout"]
    if workout["sessions_this_week"] == 0:
        patterns.append(
            {
                "type": "workout",
                "pattern": "no_workouts",
                "description": "No workout sessions logged this week.",
            }
        )
    elif workout["sessions_this_week"] >= 3:
        patterns.append(
            {
                "type": "workout",
                "pattern": "consistent_training",
                "description": f"{workout['sessions_this_week']} workouts logged this week.",
            }
        )

    tasks = stats["tasks"]
    if tasks["pending"] > 10:
        patterns.append(
            {
                "type": "productivity",
                "pattern": "task_backlog",
                "description": f"{tasks['pending']} pending tasks may indicate overload.",
            }
        )

    habits = stats["habits"]
    if habits["active"] > 0:
        completion_rate = habits["completions_this_week"] / (habits["active"] * 7) * 100
        if completion_rate < 50:
            patterns.append(
                {
                    "type": "habits",
                    "pattern": "low_habit_adherence",
                    "description": f"Habit completion rate is {completion_rate:.0f}% this week.",
                }
            )

    return patterns


async def generate_insights(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """Consolidate cross-module stats, detect patterns, and optionally enrich with AI."""
    stats = await _collect_module_stats(db, user_id)
    patterns = _detect_patterns(stats)

    insights: dict[str, Any] = {
        "stats": stats,
        "patterns": patterns,
        "recommendations": [],
        "ai_summary": None,
    }

    for pattern in patterns:
        if pattern["pattern"] == "spending_exceeds_income":
            insights["recommendations"].append(
                "Review discretionary expenses and set a weekly spending cap."
            )
        elif pattern["pattern"] == "low_study_time":
            insights["recommendations"].append(
                "Schedule short daily study blocks for topics in progress."
            )
        elif pattern["pattern"] == "no_workouts":
            insights["recommendations"].append(
                "Plan at least two workout sessions for the coming week."
            )
        elif pattern["pattern"] == "task_backlog":
            insights["recommendations"].append(
                "Prioritize and break down pending tasks into smaller actions."
            )
        elif pattern["pattern"] == "low_habit_adherence":
            insights["recommendations"].append(
                "Reduce active habits or tie them to existing routines."
            )

    if not patterns:
        insights["recommendations"].append("Keep up the current balance across life areas.")

    model = select_model("analysis")
    prompt = (
        "Analyze this personal productivity data and provide 2-3 actionable insights.\n"
        f"Data: {json.dumps(stats, ensure_ascii=False)}\n"
        f"Detected patterns: {json.dumps(patterns, ensure_ascii=False)}\n"
        "Respond in plain text, concise bullet points."
    )

    try:
        ollama = OllamaClient()
        response = await ollama.generate(
            model,
            prompt,
            system="You are a personal life analyst. Be direct and practical.",
        )
        insights["ai_summary"] = _extract_ollama_content(response)
    except OllamaError:
        insights["ai_summary"] = None

    return insights
