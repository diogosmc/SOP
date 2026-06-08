"""Auth request/response schemas."""

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
