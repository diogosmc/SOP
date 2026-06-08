"""Chat API schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.chat.models import ChatMode, MessageRole


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[uuid.UUID] = None
    mode: Optional[ChatMode] = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    model: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str]
    mode: ChatMode
    model_used: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
