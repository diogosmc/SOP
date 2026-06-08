"""Tests for brain response generator."""

from unittest.mock import AsyncMock, patch

import pytest

from app.brain.response_generator import generate_response
from app.brain.schemas import BrainAction, ConversationContext, ConversationState
from app.telegram.instructor import classify_telegram_message


def _ctx(message: str) -> ConversationContext:
    classification = classify_telegram_message(message)
    primary = classification.get("primary_intent") or classification["intent"]
    return ConversationContext(
        message=message,
        classification=classification,
        intent=primary,
        primary_intent=primary,
        secondary_intents=list(classification.get("secondary_intents") or []),
        state=ConversationState(mood="desanimado", conversation_mode="apoio"),
        is_ack=message.strip().lower() in {"não vlw", "vlw"},
    )


@pytest.mark.asyncio
async def test_ack_short_reply() -> None:
    response, model, used_fallback = await generate_response(
        "Não vlw", _ctx("Não vlw"), [], allow_llm=False
    )
    assert response in {"Tudo certo.", "👍", "Beleza.", "Combinado."}
    assert used_fallback


@pytest.mark.asyncio
async def test_emotional_fallback_not_generic() -> None:
    message = "Ah sei lá, tô afim de ficar deitado"
    response, _, used_fallback = await generate_response(
        message,
        _ctx(message),
        [BrainAction(action="update_journal", success=True)],
        allow_llm=False,
    )
    assert "tarefa" not in response.lower() or "lembrete" not in response.lower()
    assert "energia" in response.lower() or "descansar" in response.lower() or "mínima" in response.lower()
    assert used_fallback


@pytest.mark.asyncio
async def test_ollama_offline_uses_fallback() -> None:
    with patch("app.brain.response_generator.check_ollama_health", new=AsyncMock(return_value=False)):
        response, model, used_fallback = await generate_response(
            "Como organizar meu dia?",
            _ctx("Como organizar meu dia?"),
            [],
            allow_llm=True,
        )
    assert response
    assert model is None
    assert used_fallback
