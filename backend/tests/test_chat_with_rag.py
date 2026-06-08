"""Tests for chat with optional RAG context."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import get_settings
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_with_rag_injects_context(db_session, default_user_id) -> None:
    captured: list[dict] = []

    async def mock_ollama(messages, model=None):
        captured.append({"messages": messages, "model": model})
        return {"message": {"role": "assistant", "content": "Resposta com RAG"}}

    rag_context = (
        "Contexto relevante das suas notas:\n"
        "[1] For loops e while loops em Python."
    )

    with patch(
        "app.ai.rag.context_builder.build_rag_context",
        new=AsyncMock(return_value=rag_context),
    ):
        service = ChatService(db_session, ollama_chat_func=mock_ollama)
        result = await service.send_message(
            default_user_id,
            ChatMessageRequest(
                message="O que eu sei sobre loops?",
                origin="api",
                use_rag=True,
            ),
        )

    assert result.response == "Resposta com RAG"
    assert captured
    messages = captured[0]["messages"]
    assert messages[0]["role"] == "system"
    assert rag_context in messages[0]["content"]
    assert captured[0]["model"] == get_settings().ollama_model_main
