"""Chat business logic."""

import logging
import time
import uuid
from typing import Any, Callable, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaError, ollama_chat
from app.ai.prompts import SYSTEM_PROMPT, build_ollama_messages
from app.ai.router import choose_model
from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.chat.models import MessageRole
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageResult,
    ChatSessionResponse,
)

logger = logging.getLogger(__name__)

OllamaChatFunc = Callable[..., Any]
OllamaStreamFunc = Callable[..., Any]


class ChatStreamError(Exception):
    """Raised when chat streaming cannot proceed."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class StreamTurnContext:
    def __init__(
        self,
        session_id: uuid.UUID,
        model: str,
        complexity: str,
        ollama_messages: list[dict[str, str]],
        user_message: str,
    ) -> None:
        self.session_id = session_id
        self.model = model
        self.complexity = complexity
        self.ollama_messages = ollama_messages
        self.user_message = user_message


class ChatService:
    def __init__(
        self,
        db: AsyncSession,
        ollama_chat_func: Optional[OllamaChatFunc] = None,
        ollama_stream_func: Optional[OllamaStreamFunc] = None,
    ) -> None:
        self.db = db
        self.repo = ChatRepository(db)
        self._ollama_chat = ollama_chat_func or ollama_chat
        self._ollama_stream = ollama_stream_func

    async def send_message(
        self, user_id: uuid.UUID, data: ChatMessageRequest
    ) -> ChatMessageResult:
        session = await self._get_or_create_session(user_id, data)

        await self.repo.create_message(
            session.id, MessageRole.USER, data.message
        )

        history = await self.repo.list_all_messages(session.id)
        ollama_history = [
            {"role": msg.role.value, "content": msg.content} for msg in history
        ]

        settings = get_settings()
        if data.use_rag:
            from app.ai.rag.context_builder import build_rag_context

            rag_context = await build_rag_context(data.message, user_id, self.db, limit=5)
            model = settings.ollama_model_main
            messages = _build_messages_with_rag(ollama_history, rag_context)
        else:
            routing = choose_model(
                data.message,
                force_deep=data.force_deep,
                force_fast=data.force_fast,
            )
            model = routing["model"]
            messages = build_ollama_messages(ollama_history)

        started = time.perf_counter()
        try:
            result = await self._ollama_chat(messages, model=model)
        except OllamaError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama unavailable: {exc}",
            ) from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        assistant_content = _extract_assistant_content(result)

        await self.repo.create_message(
            session.id,
            MessageRole.ASSISTANT,
            assistant_content,
            model_used=model,
            response_time_ms=elapsed_ms,
        )

        if not session.title:
            title = data.message[:80] + ("..." if len(data.message) > 80 else "")
            await self.repo.update_session_title(session, title)

        await self._process_memory_safe(user_id, data.message)

        return ChatMessageResult(
            session_id=session.id,
            message=data.message,
            response=assistant_content,
            model_used=model,
            response_time_ms=elapsed_ms,
        )

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
        self, session_id: uuid.UUID, user_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedResponse[ChatMessageResponse]:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        items, total = await self.repo.list_messages(
            session_id, pagination.offset, pagination.page_size
        )
        return PaginatedResponse.create(
            [ChatMessageResponse.model_validate(m) for m in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        session = await self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        await self.repo.delete_session(session)

    async def prepare_stream_turn(
        self, user_id: uuid.UUID, data: ChatMessageRequest
    ) -> StreamTurnContext:
        """Prepare session, save user message, and build Ollama payload."""
        try:
            session = await self._get_or_create_session(user_id, data)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Session error"
            raise ChatStreamError(detail) from exc

        await self.repo.create_message(session.id, MessageRole.USER, data.message)

        history = await self.repo.list_all_messages(session.id)
        ollama_history = [
            {"role": msg.role.value, "content": msg.content} for msg in history
        ]
        routing = choose_model(
            data.message,
            force_deep=data.force_deep,
            force_fast=data.force_fast,
        )

        if not session.title:
            title = data.message[:80] + ("..." if len(data.message) > 80 else "")
            await self.repo.update_session_title(session, title)

        return StreamTurnContext(
            session_id=session.id,
            model=routing["model"],
            complexity=routing["complexity"],
            ollama_messages=build_ollama_messages(ollama_history),
            user_message=data.message,
        )

    async def finalize_stream_turn(
        self,
        session_id: uuid.UUID,
        response_text: str,
        model: str,
        response_time_ms: int,
    ) -> None:
        """Persist assistant response after streaming completes."""
        await self.repo.create_message(
            session_id,
            MessageRole.ASSISTANT,
            response_text,
            model_used=model,
            response_time_ms=response_time_ms,
        )

    async def _get_or_create_session(
        self, user_id: uuid.UUID, data: ChatMessageRequest
    ):
        if data.session_id:
            session = await self.repo.get_session(data.session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )
            return session

        return await self.repo.create_session(user_id, data.origin)

    async def _process_memory_safe(self, user_id: uuid.UUID, message: str) -> None:
        try:
            from app.modules.memory.service import MemoryService

            async with self.db.begin_nested():
                await MemoryService(self.db).process_chat_message(user_id, message)
        except Exception:
            logger.exception("memory_processing_failed")


def _extract_assistant_content(result: dict[str, Any]) -> str:
    message = result.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Invalid response from Ollama",
    )


def _build_messages_with_rag(
    history: list[dict[str, str]], rag_context: str
) -> list[dict[str, str]]:
    system_content = SYSTEM_PROMPT
    if rag_context.strip():
        system_content = f"{SYSTEM_PROMPT}\n\n{rag_context.strip()}"
    return [{"role": "system", "content": system_content}, *history]
