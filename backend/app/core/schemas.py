"""Shared API response schemas."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None


class APIError(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: APIError
