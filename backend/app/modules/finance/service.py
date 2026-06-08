"""Finance service — clean API for HTTP and future Telegram integration."""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.finance.models import TransactionType
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.schemas import (
    CategoryTotal,
    DayTotal,
    FinanceSummary,
    TransactionCreate,
    TransactionFilters,
    TransactionResponse,
    TransactionUpdate,
)


class FinanceService:
    """Business logic for personal finance transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = FinanceRepository(db)

    @staticmethod
    def build_filters(
        type_filter: Optional[TransactionType] = None,
        category: Optional[str] = None,
        start_date=None,
        end_date=None,
        search: Optional[str] = None,
    ) -> TransactionFilters:
        return TransactionFilters(
            type=type_filter,
            category=category,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )

    async def create(self, user_id: uuid.UUID, data: TransactionCreate) -> TransactionResponse:
        tx = await self.repo.create(user_id, data)
        return TransactionResponse.model_validate(tx)

    async def get(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> TransactionResponse:
        tx = await self.repo.get_by_id(transaction_id, user_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return TransactionResponse.model_validate(tx)

    async def list(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        filters: TransactionFilters,
    ) -> PaginatedResponse[TransactionResponse]:
        items, total = await self.repo.list(
            user_id, filters, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [TransactionResponse.model_validate(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate
    ) -> TransactionResponse:
        tx = await self.repo.get_by_id(transaction_id, user_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        updated = await self.repo.update(tx, data)
        return TransactionResponse.model_validate(updated)

    async def delete(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> None:
        tx = await self.repo.get_by_id(transaction_id, user_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        await self.repo.delete(tx)

    async def summary(self, user_id: uuid.UUID, filters: TransactionFilters) -> FinanceSummary:
        income, expense, count = await self.repo.summary(user_id, filters)
        return FinanceSummary(
            income=income,
            expense=expense,
            balance=income - expense,
            transactions_count=count,
        )

    async def by_category(
        self, user_id: uuid.UUID, filters: TransactionFilters
    ) -> List[CategoryTotal]:
        rows = await self.repo.by_category(user_id, filters)
        return [
            CategoryTotal(
                category=category,
                income=income,
                expense=expense,
                total=income - expense,
            )
            for category, income, expense in rows
        ]

    async def by_day(self, user_id: uuid.UUID, filters: TransactionFilters) -> List[DayTotal]:
        rows = await self.repo.by_day(user_id, filters)
        return [
            DayTotal(date=day, income=income, expense=expense, balance=income - expense)
            for day, income, expense in rows
        ]
