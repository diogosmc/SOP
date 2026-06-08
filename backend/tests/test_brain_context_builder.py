"""Tests for brain context builder."""

import pytest

from app.brain.context_builder import build_conversation_context, _estimate_context_chars
from app.brain.schemas import ConversationContext, MemorySnippet
from app.brain.state_manager import is_ack_message


@pytest.mark.asyncio
async def test_context_builder_includes_state_and_classification(db_session, default_user_id) -> None:
    context = await build_conversation_context(
        db_session, default_user_id, "Estou desanimado hoje"
    )
    assert context.intent == "emotional_checkin"
    assert context.message == "Estou desanimado hoje"
    assert context.state is not None


@pytest.mark.asyncio
async def test_context_builder_limits_size(db_session, default_user_id) -> None:
    context = await build_conversation_context(
        db_session, default_user_id, "Mensagem de teste para contexto"
    )
    assert context.context_chars <= 12000


def test_context_trim_respects_max_chars() -> None:
    context = ConversationContext(
        message="x" * 500,
        recent_messages=[{"role": "user", "content": "y" * 8000}],
        relevant_memories=[MemorySnippet(content="z" * 5000, memory_type="other")],
    )
    from app.brain.context_builder import _trim_context

    trimmed = _trim_context(context, 3000)
    assert _estimate_context_chars(trimmed) <= 3000 or len(trimmed.recent_messages) == 0


def test_is_ack_message() -> None:
    assert is_ack_message("Não vlw")
    assert is_ack_message("ok")
    assert not is_ack_message("Estou desanimado hoje")
