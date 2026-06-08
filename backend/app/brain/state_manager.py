"""User conversation state management."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.schemas import ConversationState
from app.modules.memory.state_models import UserState

_ACK_PHRASES = frozenset(
    {
        "não",
        "nao",
        "não obrigado",
        "nao obrigado",
        "não vlw",
        "nao vlw",
        "vlw",
        "valeu",
        "ok",
        "beleza",
        "show",
        "tudo certo",
        "blz",
    }
)


def is_ack_message(message: str) -> bool:
    normalized = message.strip().lower().rstrip(".! ")
    return normalized in _ACK_PHRASES


def _to_conversation_state(row: UserState) -> ConversationState:
    return ConversationState(
        mood=row.mood,
        energy=row.energy,
        current_focus=row.current_focus,
        current_topic=row.current_topic,
        conversation_mode=row.conversation_mode,
        last_intent=row.last_intent,
        last_user_message=row.last_user_message,
        last_assistant_message=row.last_assistant_message,
        metadata=dict(row.state_metadata or {}),
    )


async def get_or_create_user_state(db: AsyncSession, user_id: uuid.UUID) -> ConversationState:
    result = await db.execute(select(UserState).where(UserState.user_id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        row = UserState(user_id=user_id)
        db.add(row)
        await db.flush()
    return _to_conversation_state(row)


async def _get_row(db: AsyncSession, user_id: uuid.UUID) -> UserState:
    result = await db.execute(select(UserState).where(UserState.user_id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        row = UserState(user_id=user_id)
        db.add(row)
        await db.flush()
    return row


async def update_state_from_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    intent: str,
    classification: dict[str, Any],
) -> ConversationState:
    row = await _get_row(db, user_id)
    row.last_user_message = message[:2000]
    row.last_intent = intent

    lowered = message.lower()
    if intent == "emotional_checkin" or any(
        w in lowered for w in ("desanimado", "cansado", "culpado", "deitado", "preguiça", "preguica")
    ):
        row.mood = "desanimado"
        row.energy = "baixa"
        row.conversation_mode = "apoio"
    elif intent in {"study_log", "study_plan"} or "estud" in lowered or "revisar" in lowered:
        row.current_topic = "estudo"
        row.conversation_mode = "produtividade"
    elif intent == "appointment" or "amanhã" in lowered or "amanha" in lowered:
        row.current_topic = "agenda"
        row.conversation_mode = "organização"
    elif is_ack_message(message):
        row.conversation_mode = "normal"

    if classification.get("entities", {}).get("topic"):
        row.current_topic = str(classification["entities"]["topic"])[:128]

    await db.flush()
    return _to_conversation_state(row)


async def update_state_from_response(
    db: AsyncSession,
    user_id: uuid.UUID,
    response: str,
) -> ConversationState:
    row = await _get_row(db, user_id)
    row.last_assistant_message = response[:2000]
    await db.flush()
    return _to_conversation_state(row)
