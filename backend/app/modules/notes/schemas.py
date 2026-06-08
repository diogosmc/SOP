"""Note schemas."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = ""
    tags: Optional[List[str]] = None
    favorite: bool = False
    archived: bool = False


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    favorite: Optional[bool] = None
    archived: Optional[bool] = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    tags: Optional[List[str]]
    favorite: bool
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class ChunkSearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    similarity: float
    source_type: str
    source_id: uuid.UUID


class IndexNoteResult(BaseModel):
    document_id: uuid.UUID
    note_id: uuid.UUID
    title: str
    chunks_indexed: int
