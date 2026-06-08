"""Finance service."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.finance.models import TransactionType
from app.modules.finance.repository import FinanceRepository
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


class FinanceService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = FinanceRepository(db)

    async def create_category(
        self, user_id: uuid.UUID, data: CategoryCreate
    ) -> CategoryResponse:
        category = await self.repo.create_category(user_id, data)
        return CategoryResponse.model_validate(category)

    async def get_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> CategoryResponse:
        category = await self.repo.get_category(category_id, user_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return CategoryResponse.model_validate(category)

    async def list_categories(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[CategoryResponse]:
        items, total = await self.repo.list_categories(
            user_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [CategoryResponse.model_validate(c) for c in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_category(
        self, category_id: uuid.UUID, user_id: uuid.UUID, data: CategoryUpdate
    ) -> CategoryResponse:
        category = await self.repo.get_category(category_id, user_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        updated = await self.repo.update_category(category, data)
        return CategoryResponse.model_validate(updated)

    async def delete_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        category = await self.repo.get_category(category_id, user_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.repo.delete_category(category)

    async def create_transaction(
        self, user_id: uuid.UUID, data: TransactionCreate
    ) -> TransactionResponse:
        if data.category_id:
            category = await self.repo.get_category(data.category_id, user_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
                )
        transaction = await self.repo.create_transaction(user_id, data)
        return TransactionResponse.model_validate(transaction)

    async def get_transaction(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> TransactionResponse:
        transaction = await self.repo.get_transaction(transaction_id, user_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
        return TransactionResponse.model_validate(transaction)

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        transaction_type: Optional[TransactionType] = None,
        category_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PaginatedResponse[TransactionResponse]:
        items, total = await self.repo.list_transactions(
            user_id,
            transaction_type,
            category_id,
            start_date,
            end_date,
            pagination.offset,
            pagination.page_size,
        )
        return PaginatedResponse.create(
            [TransactionResponse.model_validate(t) for t in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_transaction(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate
    ) -> TransactionResponse:
        transaction = await self.repo.get_transaction(transaction_id, user_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
        if data.category_id:
            category = await self.repo.get_category(data.category_id, user_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
                )
        updated = await self.repo.update_transaction(transaction, data)
        return TransactionResponse.model_validate(updated)

    async def delete_transaction(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> None:
        transaction = await self.repo.get_transaction(transaction_id, user_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
        await self.repo.delete_transaction(transaction)

    async def get_summary(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> FinanceSummaryResponse:
        income, expense = await self.repo.get_summary(user_id, start_date, end_date)
        return FinanceSummaryResponse(
            period_start=start_date,
            period_end=end_date,
            income=income,
            expense=expense,
            balance=income - expense,
        )

    async def create_goal(self, user_id: uuid.UUID, data: GoalCreate) -> GoalResponse:
        goal = await self.repo.create_goal(user_id, data)
        return GoalResponse.model_validate(goal)

    async def get_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> GoalResponse:
        goal = await self.repo.get_goal(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return GoalResponse.model_validate(goal)

    async def list_goals(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[GoalResponse]:
        items, total = await self.repo.list_goals(user_id, pagination.offset, pagination.page_size)
        return PaginatedResponse.create(
            [GoalResponse.model_validate(g) for g in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def update_goal(
        self, goal_id: uuid.UUID, user_id: uuid.UUID, data: GoalUpdate
    ) -> GoalResponse:
        goal = await self.repo.get_goal(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        updated = await self.repo.update_goal(goal, data)
        return GoalResponse.model_validate(updated)

    async def delete_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> None:
        goal = await self.repo.get_goal(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await self.repo.delete_goal(goal)

    async def log_expense(
        self,
        user_id: uuid.UUID,
        *,
        amount: Decimal | float,
        description: str | None = None,
        category_name: str | None = None,
    ) -> TransactionResponse:
        category_id = None
        if category_name:
            category = await self.repo.get_or_create_category(user_id, category_name)
            category_id = category.id

        data = TransactionCreate(
            category_id=category_id,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal(str(amount)),
            description=description,
            transaction_date=date.today(),
        )
        transaction = await self.repo.create_transaction(user_id, data)
        return TransactionResponse.model_validate(transaction)
