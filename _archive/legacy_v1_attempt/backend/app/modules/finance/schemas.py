"""Finance schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.finance.models import TransactionType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    icon: Optional[str] = Field(default=None, max_length=50)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    icon: Optional[str] = Field(default=None, max_length=50)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    transaction_date: date


class TransactionUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    transaction_type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    description: Optional[str] = None
    transaction_date: Optional[date] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: Optional[uuid.UUID]
    transaction_type: TransactionType
    amount: Decimal
    description: Optional[str]
    transaction_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0)
    deadline: Optional[date] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    target_amount: Optional[Decimal] = Field(default=None, gt=0)
    current_amount: Optional[Decimal] = Field(default=None, ge=0)
    deadline: Optional[date] = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FinanceSummaryResponse(BaseModel):
    period_start: date
    period_end: date
    income: Decimal
    expense: Decimal
    balance: Decimal
