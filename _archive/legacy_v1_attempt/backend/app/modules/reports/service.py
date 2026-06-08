"""Reports service."""

import json
import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analyst import generate_insights
from app.ai.ollama import OllamaClient, OllamaError
from app.ai.router import select_model
from app.core.cache import cache_get, cache_set
from app.core.config import get_settings
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import (
    AnalyticsResponse,
    DailyReportResponse,
    GenerateWeeklyRequest,
    ModuleAnalytics,
    WeeklyReportResponse,
)


def _current_week_reference(ref_date: Optional[date] = None) -> str:
    d = ref_date or date.today()
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_dates_from_reference(week_reference: str) -> tuple[date, date]:
    year_str, week_str = week_reference.split("-W")
    year, week = int(year_str), int(week_str)
    week_start = date.fromisocalendar(year, week, 1)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


class ReportsService:
    def __init__(self, db: AsyncSession, ollama: Optional[OllamaClient] = None) -> None:
        self.repo = ReportsRepository(db)
        self.ollama = ollama or OllamaClient()

    async def get_daily(self, user_id: uuid.UUID, target_date: date) -> DailyReportResponse:
        journal = await self.repo.get_daily_journal(user_id, target_date)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No daily report for {target_date.isoformat()}",
            )
        return DailyReportResponse.model_validate(journal)

    async def get_weekly(
        self, user_id: uuid.UUID, week_reference: Optional[str] = None
    ) -> WeeklyReportResponse:
        ref = week_reference or _current_week_reference()
        review = await self.repo.get_weekly_review(user_id, ref)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No weekly report for {ref}",
            )
        return WeeklyReportResponse.model_validate(review)

    async def generate_weekly(
        self, user_id: uuid.UUID, data: GenerateWeeklyRequest
    ) -> WeeklyReportResponse:
        week_ref = data.week_reference or _current_week_reference()
        week_start, week_end = _week_dates_from_reference(week_ref)

        insights = await generate_insights(self.repo.db, user_id)

        finance_income, finance_expense, tx_count = await self.repo.get_finance_analytics(
            user_id, week_start, week_end
        )
        study_minutes, study_sessions, topics_mastered, flashcards = (
            await self.repo.get_study_analytics(user_id, week_start, week_end)
        )
        workout_sessions, workout_sets, workout_volume = await self.repo.get_workout_analytics(
            user_id, week_start, week_end
        )
        tasks_completed, tasks_pending = await self.repo.get_tasks_analytics(user_id)
        active_habits, habit_completions = await self.repo.get_habits_analytics(
            user_id, week_start, week_end
        )

        context = {
            "week_reference": week_ref,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "finance": {
                "income": finance_income,
                "expense": finance_expense,
                "transactions": tx_count,
            },
            "study": {
                "minutes": study_minutes,
                "sessions": study_sessions,
                "topics_mastered": topics_mastered,
                "flashcards": flashcards,
            },
            "workout": {
                "sessions": workout_sessions,
                "sets": workout_sets,
                "volume_kg": workout_volume,
            },
            "tasks": {"completed": tasks_completed, "pending": tasks_pending},
            "habits": {"active": active_habits, "completions": habit_completions},
            "patterns": insights.get("patterns", []),
        }

        model = select_model("report")
        prompt = (
            f"Generate a weekly personal review for week {week_ref}.\n"
            f"Data: {json.dumps(context, ensure_ascii=False)}\n"
            "Respond with JSON containing keys: summary, wins, failures, patterns, recommendations. "
            "Each value should be a string (use bullet points within the string)."
        )

        summary = wins = failures = patterns = recommendations = None
        try:
            response = await self.ollama.generate(
                model,
                prompt,
                system="You are a personal analyst. Respond with valid JSON only.",
            )
            content = response.get("response", "")
            if not content and isinstance(response.get("message"), dict):
                content = response["message"].get("content", "")
            text = content.strip()
            if text.startswith("```"):
                lines = [line for line in text.split("\n") if not line.strip().startswith("```")]
                text = "\n".join(lines).strip()
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                summary = parsed.get("summary")
                wins = parsed.get("wins")
                failures = parsed.get("failures")
                patterns = parsed.get("patterns")
                recommendations = parsed.get("recommendations")
        except (OllamaError, json.JSONDecodeError):
            summary = (
                f"Week {week_ref}: Income R${finance_income:.2f}, "
                f"expenses R${finance_expense:.2f}. "
                f"{study_minutes} min study, {workout_sessions} workouts."
            )
            patterns = json.dumps(insights.get("patterns", []), ensure_ascii=False)
            recommendations = "\n".join(insights.get("recommendations", []))

        review = await self.repo.upsert_weekly_review(
            user_id,
            week_ref,
            summary=summary,
            wins=wins,
            failures=failures,
            patterns=patterns if isinstance(patterns, str) else json.dumps(patterns),
            recommendations=recommendations,
        )
        return WeeklyReportResponse.model_validate(review)

    async def get_analytics(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AnalyticsResponse:
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=30))

        cache_key = f"analytics:{user_id}:{start.isoformat()}:{end.isoformat()}"
        settings = get_settings()
        cached = await cache_get(cache_key)
        if cached is not None:
            return AnalyticsResponse.model_validate(cached)

        finance_income, finance_expense, tx_count = await self.repo.get_finance_analytics(
            user_id, start, end
        )
        study_minutes, study_sessions, topics_mastered, flashcards = (
            await self.repo.get_study_analytics(user_id, start, end)
        )
        workout_sessions, workout_sets, workout_volume = await self.repo.get_workout_analytics(
            user_id, start, end
        )
        tasks_completed, tasks_pending = await self.repo.get_tasks_analytics(user_id)
        active_habits, habit_completions = await self.repo.get_habits_analytics(
            user_id, start, end
        )

        days = max(1, (end - start).days + 1)
        habit_adherence = (
            habit_completions / (active_habits * days) * 100 if active_habits > 0 else 0.0
        )
        task_total = tasks_completed + tasks_pending
        task_completion_rate = tasks_completed / task_total * 100 if task_total > 0 else 0.0

        modules: List[ModuleAnalytics] = [
            ModuleAnalytics(
                module="finance",
                metrics={
                    "income": finance_income,
                    "expense": finance_expense,
                    "balance": finance_income - finance_expense,
                    "transaction_count": tx_count,
                },
            ),
            ModuleAnalytics(
                module="study",
                metrics={
                    "total_minutes": study_minutes,
                    "session_count": study_sessions,
                    "topics_mastered": topics_mastered,
                    "flashcard_count": flashcards,
                },
            ),
            ModuleAnalytics(
                module="workout",
                metrics={
                    "session_count": workout_sessions,
                    "total_sets": workout_sets,
                    "total_volume_kg": workout_volume,
                },
            ),
            ModuleAnalytics(
                module="tasks",
                metrics={
                    "completed": tasks_completed,
                    "pending": tasks_pending,
                    "completion_rate": round(task_completion_rate, 1),
                },
            ),
            ModuleAnalytics(
                module="habits",
                metrics={
                    "active_habits": active_habits,
                    "completions": habit_completions,
                    "adherence_rate": round(habit_adherence, 1),
                },
            ),
        ]

        insights = await generate_insights(self.repo.db, user_id)

        result = AnalyticsResponse(
            period_start=start,
            period_end=end,
            modules=modules,
            insights=insights,
        )
        await cache_set(cache_key, result.model_dump(), settings.cache_reports_ttl)
        return result
