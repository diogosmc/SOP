"""Finance repository."""

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import (
    FinanceCategory,
    FinanceGoal,
    FinanceTransaction,
    TransactionType,
)
from app.modules.finance.schemas import (
    CategoryCreate,
    CategoryUpdate,
    GoalCreate,
    GoalUpdate,
    TransactionCreate,
    TransactionUpdate,
)


class FinanceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Categories ---

    async def create_category(self, user_id: uuid.UUID, data: CategoryCreate) -> FinanceCategory:
        category = FinanceCategory(user_id=user_id, **data.model_dump())
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def get_category(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[FinanceCategory]:
        result = await self.db.execute(
            select(FinanceCategory).where(
                FinanceCategory.id == category_id, FinanceCategory.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_category(
        self, user_id: uuid.UUID, name: str
    ) -> FinanceCategory:
        result = await self.db.execute(
            select(FinanceCategory).where(
                FinanceCategory.user_id == user_id,
                FinanceCategory.name.ilike(name),
            )
        )
        category = result.scalar_one_or_none()
        if category:
            return category

        category = FinanceCategory(user_id=user_id, name=name)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def list_categories(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[FinanceCategory], int]:
        query = (
            select(FinanceCategory)
            .where(FinanceCategory.user_id == user_id)
            .order_by(FinanceCategory.name)
            .offset(offset)
            .limit(limit)
        )
        count_query = (
            select(func.count())
            .select_from(FinanceCategory)
            .where(FinanceCategory.user_id == user_id)
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_category(
        self, category: FinanceCategory, data: CategoryUpdate
    ) -> FinanceCategory:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category: FinanceCategory) -> None:
        await self.db.delete(category)
        await self.db.flush()

    # --- Transactions ---

    async def create_transaction(
        self, user_id: uuid.UUID, data: TransactionCreate
    ) -> FinanceTransaction:
        transaction = FinanceTransaction(user_id=user_id, **data.model_dump())
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def get_transaction(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[FinanceTransaction]:
        result = await self.db.execute(
            select(FinanceTransaction).where(
                FinanceTransaction.id == transaction_id,
                FinanceTransaction.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        transaction_type: Optional[TransactionType] = None,
        category_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[FinanceTransaction], int]:
        filters = [FinanceTransaction.user_id == user_id]
        if transaction_type:
            filters.append(FinanceTransaction.transaction_type == transaction_type)
        if category_id:
            filters.append(FinanceTransaction.category_id == category_id)
        if start_date:
            filters.append(FinanceTransaction.transaction_date >= start_date)
        if end_date:
            filters.append(FinanceTransaction.transaction_date <= end_date)

        query = (
            select(FinanceTransaction)
            .where(*filters)
            .order_by(FinanceTransaction.transaction_date.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(FinanceTransaction).where(*filters)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_transaction(
        self, transaction: FinanceTransaction, data: TransactionUpdate
    ) -> FinanceTransaction:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def delete_transaction(self, transaction: FinanceTransaction) -> None:
        await self.db.delete(transaction)
        await self.db.flush()

    async def get_summary(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> Tuple[Decimal, Decimal]:
        result = await self.db.execute(
            select(
                FinanceTransaction.transaction_type,
                func.coalesce(func.sum(FinanceTransaction.amount), 0),
            )
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.transaction_date >= start_date,
                FinanceTransaction.transaction_date <= end_date,
            )
            .group_by(FinanceTransaction.transaction_type)
        )
        income = Decimal("0")
        expense = Decimal("0")
        for tx_type, total in result.all():
            if tx_type == TransactionType.INCOME:
                income = Decimal(str(total))
            elif tx_type == TransactionType.EXPENSE:
                expense = Decimal(str(total))
        return income, expense

    # --- Goals ---

    async def create_goal(self, user_id: uuid.UUID, data: GoalCreate) -> FinanceGoal:
        goal = FinanceGoal(user_id=user_id, **data.model_dump())
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    async def get_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinanceGoal]:
        result = await self.db.execute(
            select(FinanceGoal).where(FinanceGoal.id == goal_id, FinanceGoal.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_goals(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[FinanceGoal], int]:
        query = (
            select(FinanceGoal)
            .where(FinanceGoal.user_id == user_id)
            .order_by(FinanceGoal.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(FinanceGoal).where(
            FinanceGoal.user_id == user_id
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update_goal(self, goal: FinanceGoal, data: GoalUpdate) -> FinanceGoal:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    async def delete_goal(self, goal: FinanceGoal) -> None:
        await self.db.delete(goal)
        await self.db.flush()
