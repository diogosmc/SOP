"""Finance transaction repository."""

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import FinanceTransaction, TransactionType
from app.modules.finance.schemas import TransactionCreate, TransactionFilters, TransactionUpdate


class FinanceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _apply_filters(self, query, count_query, user_id: uuid.UUID, filters: TransactionFilters):
        query = query.where(FinanceTransaction.user_id == user_id)
        count_query = count_query.where(FinanceTransaction.user_id == user_id)

        if filters.type is not None:
            query = query.where(FinanceTransaction.type == filters.type)
            count_query = count_query.where(FinanceTransaction.type == filters.type)
        if filters.category:
            query = query.where(FinanceTransaction.category == filters.category)
            count_query = count_query.where(FinanceTransaction.category == filters.category)
        if filters.start_date is not None:
            query = query.where(FinanceTransaction.transaction_date >= filters.start_date)
            count_query = count_query.where(FinanceTransaction.transaction_date >= filters.start_date)
        if filters.end_date is not None:
            query = query.where(FinanceTransaction.transaction_date <= filters.end_date)
            count_query = count_query.where(FinanceTransaction.transaction_date <= filters.end_date)
        if filters.search:
            pattern = f"%{filters.search}%"
            search_clause = or_(
                FinanceTransaction.description.ilike(pattern),
                FinanceTransaction.notes.ilike(pattern),
                FinanceTransaction.category.ilike(pattern),
            )
            query = query.where(search_clause)
            count_query = count_query.where(search_clause)

        return query, count_query

    async def create(self, user_id: uuid.UUID, data: TransactionCreate) -> FinanceTransaction:
        tx = FinanceTransaction(user_id=user_id, **data.model_dump())
        self.db.add(tx)
        await self.db.flush()
        await self.db.refresh(tx)
        return tx

    async def get_by_id(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[FinanceTransaction]:
        result = await self.db.execute(
            select(FinanceTransaction).where(
                FinanceTransaction.id == transaction_id,
                FinanceTransaction.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        filters: TransactionFilters,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[FinanceTransaction], int]:
        query = select(FinanceTransaction)
        count_query = select(func.count()).select_from(FinanceTransaction)
        query, count_query = self._apply_filters(query, count_query, user_id, filters)
        query = (
            query.order_by(
                FinanceTransaction.transaction_date.desc(),
                FinanceTransaction.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar_one()

    async def update(
        self, transaction: FinanceTransaction, data: TransactionUpdate
    ) -> FinanceTransaction:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def delete(self, transaction: FinanceTransaction) -> None:
        await self.db.delete(transaction)
        await self.db.flush()

    async def summary(
        self, user_id: uuid.UUID, filters: TransactionFilters
    ) -> Tuple[Decimal, Decimal, int]:
        query = select(
            func.coalesce(
                func.sum(
                    case(
                        (FinanceTransaction.type == TransactionType.INCOME, FinanceTransaction.amount),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (FinanceTransaction.type == TransactionType.EXPENSE, FinanceTransaction.amount),
                        else_=0,
                    )
                ),
                0,
            ),
            func.count(),
        ).select_from(FinanceTransaction)
        count_query = select(func.count()).select_from(FinanceTransaction)
        query, count_query = self._apply_filters(query, count_query, user_id, filters)
        result = await self.db.execute(query)
        income, expense, count = result.one()
        return Decimal(income), Decimal(expense), int(count)

    async def by_category(
        self, user_id: uuid.UUID, filters: TransactionFilters
    ) -> List[Tuple[str, Decimal, Decimal]]:
        query = (
            select(
                FinanceTransaction.category,
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FinanceTransaction.type == TransactionType.INCOME,
                                FinanceTransaction.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FinanceTransaction.type == TransactionType.EXPENSE,
                                FinanceTransaction.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(FinanceTransaction)
            .group_by(FinanceTransaction.category)
            .order_by(FinanceTransaction.category)
        )
        count_query = select(func.count()).select_from(FinanceTransaction)
        query, _ = self._apply_filters(query, count_query, user_id, filters)
        result = await self.db.execute(query)
        return [(row[0], Decimal(row[1]), Decimal(row[2])) for row in result.all()]

    async def by_day(
        self, user_id: uuid.UUID, filters: TransactionFilters
    ) -> List[Tuple[date, Decimal, Decimal]]:
        query = (
            select(
                FinanceTransaction.transaction_date,
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FinanceTransaction.type == TransactionType.INCOME,
                                FinanceTransaction.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FinanceTransaction.type == TransactionType.EXPENSE,
                                FinanceTransaction.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(FinanceTransaction)
            .group_by(FinanceTransaction.transaction_date)
            .order_by(FinanceTransaction.transaction_date)
        )
        count_query = select(func.count()).select_from(FinanceTransaction)
        query, _ = self._apply_filters(query, count_query, user_id, filters)
        result = await self.db.execute(query)
        return [(row[0], Decimal(row[1]), Decimal(row[2])) for row in result.all()]
