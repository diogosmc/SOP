"""Tests for brain state manager."""

import pytest

from app.brain.state_manager import get_or_create_user_state, is_ack_message, update_state_from_message
from app.telegram.instructor import classify_telegram_message


@pytest.mark.asyncio
async def test_get_or_create_user_state(db_session, default_user_id) -> None:
    state = await get_or_create_user_state(db_session, default_user_id)
    assert state.conversation_mode == "normal"


@pytest.mark.asyncio
async def test_emotional_message_updates_state(db_session, default_user_id) -> None:
    classification = classify_telegram_message("Estou desanimado hoje")
    state = await update_state_from_message(
        db_session,
        default_user_id,
        "Estou desanimado hoje",
        classification["intent"],
        classification,
    )
    assert state.mood == "desanimado"
    assert state.energy == "baixa"
    assert state.conversation_mode == "apoio"


@pytest.mark.asyncio
async def test_follow_up_uses_previous_state(db_session, default_user_id) -> None:
    c1 = classify_telegram_message("Estou desanimado hoje")
    await update_state_from_message(
        db_session, default_user_id, "Estou desanimado hoje", c1["intent"], c1
    )
    c2 = classify_telegram_message("Ah sei lá, tô afim de ficar deitado")
    state = await update_state_from_message(
        db_session,
        default_user_id,
        "Ah sei lá, tô afim de ficar deitado",
        c2["intent"],
        c2,
    )
    assert state.mood == "desanimado"


def test_ack_detection() -> None:
    assert is_ack_message("vlw")
