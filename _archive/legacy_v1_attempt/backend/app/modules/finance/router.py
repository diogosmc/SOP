"""Finance API routes."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.core.pagination import PaginationParams
from app.core.schemas import APIResponse
from app.modules.finance.models import TransactionType
from app.modules.finance.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    FinanceSummaryResponse,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.modules.finance.service import FinanceService

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/categories", response_model=APIResponse[CategoryResponse])
async def create_category(
    data: CategoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CategoryResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.create_category(user_id, data))


@router.get("/categories", response_model=APIResponse)
async def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = FinanceService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_categories(user_id, pagination))


@router.get("/categories/{category_id}", response_model=APIResponse[CategoryResponse])
async def get_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CategoryResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.get_category(category_id, user_id))


@router.patch("/categories/{category_id}", response_model=APIResponse[CategoryResponse])
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CategoryResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.update_category(category_id, user_id, data))


@router.delete("/categories/{category_id}", response_model=APIResponse[None])
async def delete_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = FinanceService(db)
    await service.delete_category(category_id, user_id)
    return APIResponse(data=None)


@router.post("/transactions", response_model=APIResponse[TransactionResponse])
async def create_transaction(
    data: TransactionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.create_transaction(user_id, data))


@router.get("/transactions", response_model=APIResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    category_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = FinanceService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(
        data=await service.list_transactions(
            user_id, pagination, transaction_type, category_id, start_date, end_date
        )
    )


@router.get("/transactions/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def get_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.get_transaction(transaction_id, user_id))


@router.patch("/transactions/{transaction_id}", response_model=APIResponse[TransactionResponse])
async def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.update_transaction(transaction_id, user_id, data))


@router.delete("/transactions/{transaction_id}", response_model=APIResponse[None])
async def delete_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = FinanceService(db)
    await service.delete_transaction(transaction_id, user_id)
    return APIResponse(data=None)


@router.get("/summary", response_model=APIResponse[FinanceSummaryResponse])
async def get_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FinanceSummaryResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.get_summary(user_id, start_date, end_date))


@router.post("/goals", response_model=APIResponse[GoalResponse])
async def create_goal(
    data: GoalCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GoalResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.create_goal(user_id, data))


@router.get("/goals", response_model=APIResponse)
async def list_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    service = FinanceService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    return APIResponse(data=await service.list_goals(user_id, pagination))


@router.get("/goals/{goal_id}", response_model=APIResponse[GoalResponse])
async def get_goal(
    goal_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GoalResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.get_goal(goal_id, user_id))


@router.patch("/goals/{goal_id}", response_model=APIResponse[GoalResponse])
async def update_goal(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GoalResponse]:
    service = FinanceService(db)
    return APIResponse(data=await service.update_goal(goal_id, user_id, data))


@router.delete("/goals/{goal_id}", response_model=APIResponse[None])
async def delete_goal(
    goal_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    service = FinanceService(db)
    await service.delete_goal(goal_id, user_id)
    return APIResponse(data=None)
