"""Reports API routes."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    TTL_ANALYTICS,
    TTL_DASHBOARD,
    TTL_INSIGHTS,
    build_cache_key,
    get_or_set_json,
    invalidate_user_cache,
)
from app.core.config import get_settings
from app.core.deps import get_current_user_id, get_db
from app.core.schemas import APIResponse
from app.modules.reports.schemas import (
    AnalyticsResponse,
    DailyReport,
    InsightsResponse,
    RebuildDailyResponse,
    WeeklyReport,
)
from app.modules.reports.service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=APIResponse[DailyReport])
async def get_daily_report(
    target_date: Optional[date] = Query(None, alias="date"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DailyReport]:
    service = ReportsService(db)
    date_key = target_date.isoformat() if target_date else "today"
    cache_key = build_cache_key("reports:daily", user_id, date_key)

    async def load() -> DailyReport:
        return await service.daily_report(user_id, target_date)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_DASHBOARD, load)
    else:
        data = await load()
    return APIResponse(data=DailyReport.model_validate(data))


@router.get("/weekly", response_model=APIResponse[WeeklyReport])
async def get_weekly_report(
    ref_date: Optional[date] = Query(None, alias="date"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[WeeklyReport]:
    service = ReportsService(db)
    date_key = ref_date.isoformat() if ref_date else "current"
    cache_key = build_cache_key("reports:weekly", user_id, date_key)

    async def load() -> WeeklyReport:
        return await service.weekly_report(user_id, ref_date)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_DASHBOARD, load)
    else:
        data = await load()
    return APIResponse(data=WeeklyReport.model_validate(data))


@router.get("/analytics", response_model=APIResponse[AnalyticsResponse])
async def get_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AnalyticsResponse]:
    service = ReportsService(db)
    cache_key = build_cache_key(
        "reports:analytics",
        user_id,
        start_date.isoformat() if start_date else "none",
        end_date.isoformat() if end_date else "none",
    )

    async def load() -> AnalyticsResponse:
        return await service.analytics(user_id, start_date, end_date)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_ANALYTICS, load)
    else:
        data = await load()
    return APIResponse(data=AnalyticsResponse.model_validate(data))


@router.get("/insights", response_model=APIResponse[InsightsResponse])
async def get_insights(
    use_ai: bool = Query(False),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InsightsResponse]:
    service = ReportsService(db)
    cache_key = build_cache_key("reports:insights", user_id, "ai" if use_ai else "rules")

    async def load() -> InsightsResponse:
        return await service.insights(user_id, use_ai=use_ai)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_INSIGHTS, load)
    else:
        data = await load()
    return APIResponse(data=InsightsResponse.model_validate(data))


@router.post("/rebuild-daily", response_model=APIResponse[RebuildDailyResponse])
async def rebuild_daily_report(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RebuildDailyResponse]:
    service = ReportsService(db)
    result = await service.rebuild_daily(user_id)
    await invalidate_user_cache(user_id, "reports")
    return APIResponse(data=result)
