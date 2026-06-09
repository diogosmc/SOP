"""Silent background extraction — journal, memory, structured actions (no user-facing text)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.action_executor import execute_actions
from app.brain.companion import is_social_greeting
from app.brain.llm_policy import _has_finance_keyword
from app.brain.schemas import BrainAction, ConversationContext
from app.brain.tool_router import decide_actions

logger = logging.getLogger(__name__)

_STRUCTURED_ONLY = frozenset(
    {
        "expense_log",
        "note_creation",
        "task_creation",
        "workout_log",
        "study_log",
    }
)

_SOFT_COLLECT = frozenset(
    {
        "general_chat",
        "emotional_checkin",
        "question",
        "planning_request",
        "routine_planning",
        "study_plan",
    }
)


def _soft_actions(message: str, context: ConversationContext) -> list[BrainAction]:
    primary = context.primary_intent or context.intent
    actions: list[BrainAction] = [
        BrainAction(action="update_journal", params={"message": message}),
    ]
    if context.classification.get("should_save_memory") or primary in {
        "emotional_checkin",
        "planning_request",
        "study_plan",
    }:
        actions.append(
            BrainAction(
                action="create_memory",
                params={
                    "content": message,
                    "memory_type": "context",
                    "confidence": 0.5,
                },
            )
        )
    return actions


async def collect_conversation_data(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    context: ConversationContext,
) -> list[BrainAction]:
    """Run after companion reply — persist context without blocking chat."""
    if is_social_greeting(message):
        return [BrainAction(action="none")]

    primary = context.primary_intent or context.intent

    if primary == "expense_log" and not _has_finance_keyword(message):
        actions = _soft_actions(message, context)
    elif primary in _SOFT_COLLECT or primary == "study_log":
        actions = _soft_actions(message, context)
    elif primary not in _STRUCTURED_ONLY and not context.classification.get(
        "explicit_appointment"
    ):
        actions = decide_actions(message, context)
        if any(a.action in {"create_task", "create_reminder"} for a in actions):
            actions = _soft_actions(message, context)
    else:
        actions = decide_actions(message, context)

    try:
        executed = await execute_actions(db, user_id, actions, context.classification)
        logger.info(
            "brain_background_collected user_id=%s intent=%s actions=%s",
            user_id,
            primary,
            [(a.action, a.success) for a in executed],
        )
        return executed
    except Exception:
        logger.exception("brain_background_collect_failed user_id=%s", user_id)
        return [BrainAction(action="none", success=False)]
