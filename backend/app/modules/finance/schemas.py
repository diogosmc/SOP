"""Finance schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.finance.models import TransactionType


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    type: TransactionType
    category: str = Field(min_length=1, max_length=100)
    transaction_date: date
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    transaction_date: Optional[date] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    description: str
    amount: Decimal
    type: TransactionType
    category: str
    transaction_date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FinanceSummary(BaseModel):
    income: Decimal
    expense: Decimal
    balance: Decimal
    transactions_count: int


class CategoryTotal(BaseModel):
    category: str
    income: Decimal
    expense: Decimal
    total: Decimal


class DayTotal(BaseModel):
    date: date
    income: Decimal
    expense: Decimal
    balance: Decimal


class TransactionFilters(BaseModel):
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
