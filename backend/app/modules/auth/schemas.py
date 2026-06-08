"""Auth schemas."""

import re
import uuid
from typing import Annotated, Optional

from pydantic import BaseModel, Field, PlainValidator

_LOCAL_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not _LOCAL_EMAIL_RE.match(email):
        raise ValueError("Invalid email address")
    return email


LocalEmail = Annotated[str, PlainValidator(_normalize_email)]


class LoginRequest(BaseModel):
    email: LocalEmail
    password: str = Field(min_length=1, max_length=128)


class BootstrapAdminRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: LocalEmail
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: Optional[str]
    is_active: bool
    is_admin: bool
    timezone: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: Optional[str] = None


class BootstrapAvailableResponse(BaseModel):
    available: bool
    auth_enabled: bool
