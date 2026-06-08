"""Tests for chat service."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.ai.ollama import OllamaError
from app.core.pagination import PaginationParams
from app.modules.chat.models import ChatMessage, ChatSession, MessageRole
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService


async def _mock_ollama_success(*args, **kwargs) -> dict:
    return {"message": {"role": "assistant", "content": "Resposta da IA"}}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_message_creates_session_automatically(
    db_session, default_user_id
) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    result = await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Olá, copiloto", origin="api"),
    )

    assert result.session_id is not None
    assert result.message == "Olá, copiloto"
    assert result.response == "Resposta da IA"
    assert result.model_used
    assert result.response_time_ms >= 0

    session = await db_session.get(ChatSession, result.session_id)
    assert session is not None
    assert session.title == "Olá, copiloto"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_message_saves_user_and_assistant_messages(
    db_session, default_user_id
) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    result = await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Como organizar o dia?", origin="api"),
    )

    messages_result = await db_session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == result.session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = list(messages_result.scalars().all())
    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "Como organizar o dia?"
    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[1].content == "Resposta da IA"
    assert messages[1].model_used == result.model_used
    assert messages[1].response_time_ms is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_message_reuses_existing_session(
    db_session, default_user_id
) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)

    first = await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Primeira mensagem", origin="api"),
    )
    second = await service.send_message(
        default_user_id,
        ChatMessageRequest(
            message="Segunda mensagem",
            session_id=first.session_id,
            origin="api",
        ),
    )

    assert second.session_id == first.session_id

    messages_result = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == first.session_id)
    )
    assert len(list(messages_result.scalars().all())) == 4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_sessions(db_session, default_user_id) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Sessão teste", origin="dashboard"),
    )

    from app.core.pagination import PaginationParams

    result = await service.list_sessions(default_user_id, PaginationParams())
    assert result.total >= 1
    assert result.items[0].origin.value == "dashboard"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_messages(db_session, default_user_id) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    sent = await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Mensagem listável", origin="api"),
    )

    pagination = PaginationParams(page=1, page_size=50)
    result = await service.list_messages(sent.session_id, default_user_id, pagination)
    assert len(result.items) == 2
    assert result.items[0].role == MessageRole.USER


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_session(db_session, default_user_id) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    sent = await service.send_message(
        default_user_id,
        ChatMessageRequest(message="Para deletar", origin="api"),
    )

    await service.delete_session(sent.session_id, default_user_id)

    session = await db_session.get(ChatSession, sent.session_id)
    assert session is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_failure_returns_controlled_error(
    db_session, default_user_id
) -> None:
    async def _mock_ollama_fail(*args, **kwargs) -> dict:
        raise OllamaError("offline")

    service = ChatService(db_session, ollama_chat_func=_mock_ollama_fail)

    with pytest.raises(HTTPException) as exc_info:
        await service.send_message(
            default_user_id,
            ChatMessageRequest(message="vai falhar", origin="api"),
        )

    assert exc_info.value.status_code == 502
    assert "Ollama unavailable" in str(exc_info.value.detail)

    messages_result = await db_session.execute(select(ChatMessage))
    user_messages = [
        m for m in messages_result.scalars().all() if m.role == MessageRole.USER
    ]
    assert any(m.content == "vai falhar" for m in user_messages)
