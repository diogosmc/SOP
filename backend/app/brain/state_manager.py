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

_EXPLICIT_PRODUCTIVITY_INTENTS = frozenset(
    {
        "workout_log",
        "study_plan",
        "study_log",
        "expense_log",
        "task_creation",
        "note_creation",
    }
)

_EMOTIONAL_MARKERS = (
    "desanimado",
    "cansado",
    "cansada",
    "culpado",
    "culpada",
    "deitado",
    "deitada",
    "preguiça",
    "preguica",
    "sem vontade",
)

_FINANCE_GOAL_MARKERS = (
    "final do mes",
    "final do mês",
    "nao posso gastar",
    "não posso gastar",
    "juntar dinheiro",
    "comprar moto",
    "meu objetivo",
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


async def reset_user_state(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Clear accumulated mood/topic between benchmark messages."""
    row = await _get_row(db, user_id)
    row.mood = None
    row.energy = None
    row.current_focus = None
    row.current_topic = None
    row.conversation_mode = "normal"
    row.last_intent = None
    row.state_metadata = {}
    await db.flush()


async def update_state_from_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    intent: str,
    classification: dict[str, Any],
) -> ConversationState:
    row = await _get_row(db, user_id)
    row.last_user_message = message[:2000]

    primary = classification.get("primary_intent") or intent
    secondary = list(classification.get("secondary_intents") or [])
    row.last_intent = primary
    lowered = message.lower()

    if primary in _EXPLICIT_PRODUCTIVITY_INTENTS:
        row.mood = None
        row.energy = None
        row.conversation_mode = "produtividade"
        if primary in {"study_log", "study_plan"} or "estud" in lowered or "revisar" in lowered:
            row.current_topic = "estudo"
        elif primary == "workout_log":
            row.current_topic = "treino"
    elif primary in {"routine_planning", "appointment"}:
        row.current_topic = "agenda"
        row.conversation_mode = "organização"
        if primary == "routine_planning" and "emotional_checkin" not in secondary:
            pass
    elif primary == "goal_update" or any(m in lowered for m in _FINANCE_GOAL_MARKERS):
        row.conversation_mode = "normal"
        if "moto" in lowered or "juntar" in lowered:
            row.current_topic = "finanças"
    elif primary == "emotional_checkin" or (
        "emotional_checkin" in secondary
        and primary not in _EXPLICIT_PRODUCTIVITY_INTENTS
        and primary != "routine_planning"
    ):
        row.mood = "desanimado"
        row.energy = "baixa"
        row.conversation_mode = "apoio"
    elif any(marker in lowered for marker in _EMOTIONAL_MARKERS) and primary == "general_chat":
        row.mood = "desanimado"
        row.energy = "baixa"
        row.conversation_mode = "apoio"
    elif is_ack_message(message):
        row.conversation_mode = "normal"

    if secondary:
        metadata = dict(row.state_metadata or {})
        metadata["mixed"] = True
        metadata["secondary"] = secondary
        row.state_metadata = metadata

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
