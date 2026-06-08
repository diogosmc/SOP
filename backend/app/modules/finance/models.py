"""Finance models."""

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class FinanceTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "finance_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            name="finance_transaction_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="finance_transactions")
