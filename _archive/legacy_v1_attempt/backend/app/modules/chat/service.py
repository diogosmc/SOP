"""Chat business logic."""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.ai.router import select_model
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.chat.models import ChatMode, MessageRole
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
)


class ChatService:
    def __init__(self, db: AsyncSession, ollama: Optional[OllamaClient] = None) -> None:
        self.repo = ChatRepository(db)
        self.ollama = ollama or OllamaClient()

    async def send_message(
        self, user_id: uuid.UUID, data: ChatMessageRequest
    ) -> ChatMessageResponse:
        session = await self._get_or_create_session(user_id, data)
        await self.repo.create_message(
            session.id, user_id, MessageRole.USER, data.message
        )

        history = await self.repo.list_messages(session.id, user_id)
        model = select_model(mode=session.mode, message=data.message)
        ollama_messages = [
            {"role": msg.role.value, "content": msg.content} for msg in history
        ]

        try:
            response_text = await self.ollama.chat(model, ollama_messages)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {exc}",
            ) from exc

        assistant_msg = await self.repo.create_message(
            session.id, user_id, MessageRole.ASSISTANT, response_text, model=model
        )

        title = session.title
        if not title:
            title = data.message[:80] + ("..." if len(data.message) > 80 else "")

        await self.repo.update_session(
            session,
            title=title,
            model_used=model,
            increment_messages=2,
        )

        return ChatMessageResponse.model_validate(assistant_msg)

    async def list_sessions(
        self, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[ChatSessionResponse]:
        items, total = await self.repo.list_sessions(
            user_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [ChatSessionResponse.model_validate(s) for s in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def list_messages(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[ChatMessageResponse]:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        messages = await self.repo.list_messages(session_id, user_id)
        return [ChatMessageResponse.model_validate(m) for m in messages]

    async def _get_or_create_session(
        self, user_id: uuid.UUID, data: ChatMessageRequest
    ):
        if data.session_id:
            session = await self.repo.get_session(data.session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
                )
            return session

        mode = data.mode or ChatMode.GENERAL
        return await self.repo.create_session(user_id, mode=mode)
