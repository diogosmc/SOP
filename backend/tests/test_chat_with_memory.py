"""Tests for chat integration with evolutionary memory."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService
from app.modules.memory.models import AIMemory, MemoryType


async def _mock_ollama_success(*args, **kwargs) -> dict:
    return {"message": {"role": "assistant", "content": "Entendi seu objetivo."}}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_creates_memory_for_goal(db_session, default_user_id) -> None:
    service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
    await service.send_message(
        default_user_id,
        ChatMessageRequest(
            message="Quero passar em Medicina",
            origin="api",
        ),
    )

    result = await db_session.execute(
        select(AIMemory).where(
            AIMemory.user_id == default_user_id,
            AIMemory.type == MemoryType.GOAL,
        )
    )
    memories = list(result.scalars().all())
    assert memories
    assert any("medicina" in memory.content.lower() for memory in memories)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_extractor_failure_does_not_break_chat(
    db_session, default_user_id
) -> None:
    with patch(
        "app.modules.memory.service.extract_memory_candidates",
        side_effect=RuntimeError("memory extractor failed"),
    ):
        service = ChatService(db_session, ollama_chat_func=_mock_ollama_success)
        result = await service.send_message(
            default_user_id,
            ChatMessageRequest(message="Quero passar em Medicina", origin="api"),
        )

    assert result.response == "Entendi seu objetivo."
