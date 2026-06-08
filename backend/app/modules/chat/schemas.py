"""Chat API schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.chat.models import ChatOrigin, MessageRole


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[uuid.UUID] = None
    origin: ChatOrigin = ChatOrigin.API
    force_fast: bool = False
    force_deep: bool = False
    use_rag: bool = False


class ChatMessageResult(BaseModel):
    session_id: uuid.UUID
    message: str
    response: str
    model_used: str
    response_time_ms: int


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    origin: ChatOrigin
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    model_used: Optional[str]
    response_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
