"""Note schemas."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = ""
    tags: Optional[List[str]] = None
    is_favorite: bool = False


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    tags: Optional[List[str]]
    is_favorite: bool
    is_indexed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
