"""Finance API routes."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    TTL_DASHBOARD,
    build_cache_key,
    get_or_set_json,
    invalidate_user_cache,
)
from app.core.config import get_settings
from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.finance.models import TransactionType
from app.modules.finance.schemas import (
    CategoryTotal,
    DayTotal,
    FinanceSummary,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.modules.finance.service import FinanceService

router = APIRouter(prefix="/finance", tags=["finance"])


def _filter_params(
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
):
    return FinanceService.build_filters(type, category, start_date, end_date, search)


@router.post("/transactions", response_model=APIResponse[TransactionResponse])
async def create_transaction(
    data: TransactionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    result = await service.create(user_id, data)
    await invalidate_user_cache(user_id, "finance:summary")
    return APIResponse(data=result)


@router.get("/transactions", response_model=APIResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = FinanceService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = _filter_params(type, category, start_date, end_date, search)
    return APIResponse(data=await service.list(user_id, pagination, filters))


@router.get("/summary", response_model=APIResponse[FinanceSummary])
async def finance_summary(
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FinanceSummary]:
    service = FinanceService(db)
    filters = _filter_params(type, category, start_date, end_date, search)
    cache_key = build_cache_key(
        "finance:summary",
        user_id,
        str(type) if type else "all",
        category or "all",
        start_date.isoformat() if start_date else "none",
        end_date.isoformat() if end_date else "none",
        search or "none",
    )

    async def load() -> FinanceSummary:
        return await service.summary(user_id, filters)

    if get_settings().cache_enabled:
        data = await get_or_set_json(cache_key, TTL_DASHBOARD, load)
    else:
        data = await load()
    return APIResponse(data=FinanceSummary.model_validate(data))


@router.get("/by-category", response_model=APIResponse[list[CategoryTotal]])
async def finance_by_category(
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[CategoryTotal]]:
    service = FinanceService(db)
    filters = _filter_params(type, category, start_date, end_date, search)
    return APIResponse(data=await service.by_category(user_id, filters))


@router.get("/by-day", response_model=APIResponse[list[DayTotal]])
async def finance_by_day(
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = FinanceService(db)
    filters = _filter_params(type, category, start_date, end_date, search)
    return APIResponse(data=await service.by_day(user_id, filters))


@router.get("/transactions/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def get_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.get(transaction_id, user_id))


@router.patch("/transactions/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    result = await service.update(transaction_id, user_id, data)
    await invalidate_user_cache(user_id, "finance:summary")
    return APIResponse(data=result)


@router.delete("/transactions/{transaction_id}", response_model=APIResponse[None])
async def delete_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = FinanceService(db)
    await service.delete(transaction_id, user_id)
    await invalidate_user_cache(user_id, "finance:summary")
    return APIResponse(data=None)
