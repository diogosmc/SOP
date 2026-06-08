"""Reports API routes."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.schemas import APIResponse
from app.modules.reports.schemas import (
    AnalyticsResponse,
    DailyReportResponse,
    GenerateWeeklyRequest,
    WeeklyReportResponse,
)
from app.modules.reports.service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=APIResponse[DailyReportResponse])
async def get_daily_report(
    report_date: date = Query(default_factory=date.today, alias="date"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DailyReportResponse]:
    service = ReportsService(db)
    return APIResponse(data=await service.get_daily(user_id, report_date))


@router.get("/weekly", response_model=APIResponse[WeeklyReportResponse])
async def get_weekly_report(
    week_reference: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WeeklyReportResponse]:
    service = ReportsService(db)
    return APIResponse(data=await service.get_weekly(user_id, week_reference))


@router.post("/generate-weekly", response_model=APIResponse[WeeklyReportResponse])
async def generate_weekly_report(
    data: GenerateWeeklyRequest = GenerateWeeklyRequest(),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WeeklyReportResponse]:
    service = ReportsService(db)
    return APIResponse(data=await service.generate_weekly(user_id, data))


@router.get("/analytics", response_model=APIResponse[AnalyticsResponse])
async def get_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AnalyticsResponse]:
    service = ReportsService(db)
    return APIResponse(data=await service.get_analytics(user_id, start_date, end_date))
