"""Reports service."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Awaitable, Callable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analyst import generate_ai_insights
from app.modules.memory.service import MemoryService
from app.modules.reports.repository import ReportsRepository, week_bounds
from app.modules.reports.schemas import (
    AnalyticsResponse,
    CategoryAmount,
    DailyReport,
    DayAmount,
    HabitsAnalytics,
    InsightsResponse,
    RebuildDailyResponse,
    WeeklyReport,
)
from app.scheduler.summaries import build_daily_summary

OllamaChatFuncType = Callable[..., Awaitable[dict[str, Any]]]


class ReportsService:
    def __init__(
        self,
        db: AsyncSession,
        ollama_chat_func: Optional[OllamaChatFuncType] = None,
    ) -> None:
        self.db = db
        self.repo = ReportsRepository(db)
        self._ollama_chat = ollama_chat_func

    async def daily_report(self, user_id: uuid.UUID, target_date: Optional[date] = None) -> DailyReport:
        day = target_date or date.today()
        journal = await self.repo.get_journal(user_id, day)
        tasks_completed, tasks_pending = await self.repo.daily_tasks(user_id, day)
        habits_active = await self.repo.habits_active_count(user_id)
        study_minutes = await self.repo.study_minutes_on_date(user_id, day)
        workout_completed = await self.repo.workout_completed_on_date(user_id, day)
        income, expense = await self.repo.finance_on_date(user_id, day)

        mood = journal.mood_score if journal else None
        productivity = journal.productivity_score if journal else None
        if productivity is None:
            productivity = self._estimate_productivity(
                tasks_completed, study_minutes, workout_completed, income, expense
            )

        summary = journal.summary if journal and journal.summary else None
        if not summary:
            summary = await build_daily_summary(user_id, self.db)

        return DailyReport(
            date=day,
            tasks_completed=tasks_completed,
            tasks_pending=tasks_pending,
            habits_active=habits_active,
            study_minutes=study_minutes,
            workout_completed=workout_completed,
            income=income,
            expense=expense,
            balance=income - expense,
            mood_score=mood,
            productivity_score=productivity,
            summary=summary,
        )

    async def weekly_report(self, user_id: uuid.UUID, ref_date: Optional[date] = None) -> WeeklyReport:
        ref = ref_date or date.today()
        start, end = week_bounds(ref)
        prev_start = start - timedelta(days=7)
        prev_end = start - timedelta(days=1)

        tasks_completed = await self.repo.weekly_tasks_completed(user_id, start, end)
        study_minutes = await self.repo.study_minutes_in_range(user_id, start, end)
        workouts_completed = await self.repo.workouts_completed_in_range(user_id, start, end)
        finance_balance = await self.repo.finance_balance_in_range(user_id, start, end)
        habits_summary = await self.repo.habits_week_summary(user_id, start, end)

        prev_study = await self.repo.study_minutes_in_range(user_id, prev_start, prev_end)
        prev_workouts = await self.repo.workouts_completed_in_range(user_id, prev_start, prev_end)
        pending = await self.repo.pending_tasks_count(user_id)
        days_no_workout = await self.repo.days_since_last_workout(user_id, end)
        top_expense = await self.repo.top_expense_category(user_id, start, end)

        wins: List[str] = []
        problems: List[str] = []
        recommendations: List[str] = []

        if tasks_completed > 0:
            wins.append(f"Você concluiu {tasks_completed} tarefa(s) esta semana.")
        if study_minutes >= 60:
            wins.append(f"Registrou {study_minutes} minutos de estudo.")
        if workouts_completed >= 2:
            wins.append(f"Completou {workouts_completed} treino(s).")
        if finance_balance > 0:
            wins.append(f"Saldo positivo de R$ {finance_balance:.2f} no período.")

        if study_minutes > prev_study and prev_study > 0:
            wins.append("Você estudou mais nesta semana do que na anterior.")
        elif study_minutes < prev_study and prev_study >= 30:
            problems.append("Seus minutos de estudo caíram em relação à semana anterior.")

        if pending >= 10:
            problems.append(f"Você tem {pending} tarefas pendentes ou em progresso.")
        if days_no_workout is not None and days_no_workout >= 4:
            problems.append(f"Você está há {days_no_workout} dia(s) sem registrar treino.")
        if top_expense and top_expense[1] > Decimal("500"):
            problems.append(f"Seus gastos com {top_expense[0]} estão altos (R$ {top_expense[1]:.2f}).")
        if workouts_completed < prev_workouts and prev_workouts > 0:
            problems.append("Menos treinos registrados do que na semana passada.")

        if not wins:
            wins.append("Semana ainda sem destaques — pequenos passos contam.")
        if not problems:
            problems.append("Nenhum alerta crítico identificado.")

        if pending >= 5:
            recommendations.append("Priorize concluir tarefas pendentes antes de abrir novas.")
        if study_minutes < 120:
            recommendations.append("Tente reservar blocos curtos de estudo na rotina.")
        if days_no_workout is None or days_no_workout >= 3:
            recommendations.append("Registre pelo menos um treino esta semana, se fizer sentido para você.")
        if top_expense:
            recommendations.append(f"Revise gastos na categoria {top_expense[0]}.")
        if not recommendations:
            recommendations.append("Mantenha a consistência nos módulos que já funcionam bem.")

        return WeeklyReport(
            week_start=start,
            week_end=end,
            tasks_completed=tasks_completed,
            study_minutes=study_minutes,
            workouts_completed=workouts_completed,
            finance_balance=finance_balance,
            habits_summary=habits_summary,
            wins=wins,
            problems=problems,
            recommendations=recommendations,
        )

    async def analytics(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AnalyticsResponse:
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=29))

        tasks_by_status = await self.repo.tasks_by_status(user_id)
        finance_rows = await self.repo.finance_by_category(user_id, start, end)
        study_rows = await self.repo.study_minutes_by_day(user_id, start, end)
        workout_rows = await self.repo.workouts_by_day(user_id, start, end)
        active, positive, negative = await self.repo.habits_counts(user_id)
        memories = await self.repo.memories_by_type(user_id)

        return AnalyticsResponse(
            period_start=start,
            period_end=end,
            tasks_by_status=tasks_by_status,
            finance_by_category=[
                CategoryAmount(
                    category=cat,
                    income=inc,
                    expense=exp,
                    total=inc - exp,
                )
                for cat, inc, exp in finance_rows
            ],
            study_minutes_by_day=[DayAmount(date=d, value=v) for d, v in study_rows],
            workouts_by_day=[DayAmount(date=d, value=v) for d, v in workout_rows],
            habits=HabitsAnalytics(active=active, positive=positive, negative=negative),
            memories_by_type=memories,
        )

    async def insights(self, user_id: uuid.UUID, use_ai: bool = False) -> InsightsResponse:
        today = date.today()
        start, end = week_bounds(today)
        prev_start = start - timedelta(days=7)
        prev_end = start - timedelta(days=1)

        study_week = await self.repo.study_minutes_in_range(user_id, start, end)
        study_prev = await self.repo.study_minutes_in_range(user_id, prev_start, prev_end)
        pending = await self.repo.pending_tasks_count(user_id)
        days_no_workout = await self.repo.days_since_last_workout(user_id, today)
        top_expense = await self.repo.top_expense_category(user_id, start, end)
        workouts_week = await self.repo.workouts_completed_in_range(user_id, start, end)

        rule_insights: List[str] = []

        if study_week > study_prev and study_prev > 0:
            rule_insights.append("Você estudou mais nesta semana do que na anterior.")
        elif study_week == 0 and study_prev > 0:
            rule_insights.append("Nenhum minuto de estudo registrado esta semana ainda.")

        if top_expense and top_expense[1] > Decimal("300"):
            rule_insights.append(f"Seus gastos com {top_expense[0]} estão altos.")

        if days_no_workout is not None and days_no_workout >= 3:
            rule_insights.append(f"Você está há {days_no_workout} dia(s) sem registrar treino.")
        elif workouts_week >= 3:
            rule_insights.append(f"Boa consistência: {workouts_week} treinos registrados esta semana.")

        if pending >= 8:
            rule_insights.append(f"Você tem {pending} tarefas pendentes — considere priorizar.")

        daily = await self.daily_report(user_id, today)
        if daily.tasks_completed > 0:
            rule_insights.append(f"Hoje você já concluiu {daily.tasks_completed} tarefa(s).")

        if not rule_insights:
            rule_insights.append("Continue registrando atividades para insights mais precisos.")

        ai_used = False
        if use_ai:
            context = {
                "study_minutes_week": study_week,
                "study_minutes_prev_week": study_prev,
                "pending_tasks": pending,
                "days_since_workout": days_no_workout,
                "workouts_this_week": workouts_week,
                "top_expense_category": top_expense[0] if top_expense else None,
                "top_expense_amount": float(top_expense[1]) if top_expense else 0,
            }
            ai_items = await generate_ai_insights(context, self._ollama_chat)
            if ai_items:
                ai_used = True
                rule_insights = ai_items

        return InsightsResponse(
            insights=rule_insights,
            source="ai" if ai_used else "rules",
            ai_used=ai_used,
        )

    async def rebuild_daily(self, user_id: uuid.UUID) -> RebuildDailyResponse:
        memory_service = MemoryService(self.db)
        await memory_service.rebuild_today_journal(user_id)
        report = await self.daily_report(user_id, date.today())
        return RebuildDailyResponse(rebuilt=True, report=report)

    @staticmethod
    def _estimate_productivity(
        tasks_completed: int,
        study_minutes: int,
        workout_completed: bool,
        income: Decimal,
        expense: Decimal,
    ) -> float:
        score = 0.0
        score += min(tasks_completed * 15, 45)
        score += min(study_minutes / 2, 30)
        if workout_completed:
            score += 15
        if income > expense:
            score += 10
        return round(min(score, 100.0), 1)
