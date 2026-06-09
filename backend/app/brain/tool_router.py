"""Decide automatic actions from message and context."""

from __future__ import annotations

from app.brain.schemas import BrainAction, ConversationContext
from app.brain.state_manager import is_ack_message


def decide_actions(
    message: str,
    context: ConversationContext,
) -> list[BrainAction]:
    if context.is_ack or is_ack_message(message):
        return [BrainAction(action="none")]

    intent = context.primary_intent or context.intent
    entities = context.classification.get("entities") or {}
    actions: list[BrainAction] = []

    if intent == "routine_planning":
        actions.extend(
            [
                BrainAction(action="create_memory", params={"content": message}),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif intent == "appointment":
        actions.extend(
            [
                BrainAction(action="create_memory", params={"content": message}),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )
        if context.classification.get("explicit_appointment") and (
            entities.get("remind_at") or entities.get("title")
        ):
            actions.append(
                BrainAction(
                    action="create_reminder",
                    params={
                        "title": entities.get("title", "Compromisso"),
                        "remind_at": entities.get("remind_at"),
                    },
                )
            )
            actions.append(
                BrainAction(
                    action="create_task",
                    params={
                        "title": entities.get("title", "Compromisso"),
                        "due_date": entities.get("remind_at"),
                        "category": "compromisso",
                    },
                )
            )

    elif intent in {"study_plan", "task_creation"}:
        deferral = context.classification.get("study_deferral", False)
        if deferral:
            actions.extend(
                [
                    BrainAction(action="create_memory", params={"content": message}),
                    BrainAction(action="update_journal", params={"message": message}),
                ]
            )
        else:
            actions.extend(
                [
                    BrainAction(
                        action="create_task",
                        params={
                            "title": entities.get("title", message[:120]),
                            "due_date": entities.get("remind_at"),
                            "category": "estudo" if intent == "study_plan" else None,
                        },
                    ),
                    BrainAction(action="update_journal", params={"message": message}),
                    BrainAction(action="create_memory", params={"content": message}),
                ]
            )

    elif intent == "study_log":
        actions.extend(
            [
                BrainAction(action="create_study_log", params={"message": message}),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif intent == "expense_log":
        actions.extend(
            [
                BrainAction(
                    action="create_finance_transaction",
                    params={"message": message, "entities": entities},
                ),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif intent == "emotional_checkin":
        actions.extend(
            [
                BrainAction(
                    action="create_memory",
                    params={"content": message, "confidence": 0.6, "memory_type": "emotional"},
                ),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif intent == "note_creation":
        actions.append(
            BrainAction(
                action="create_note",
                params={
                    "title": entities.get("title", "Nota"),
                    "content": entities.get("content", message),
                },
            )
        )

    elif intent == "workout_log":
        actions.extend(
            [
                BrainAction(action="create_workout_log", params={"message": message}),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif intent == "goal_update":
        actions.extend(
            [
                BrainAction(
                    action="create_memory",
                    params={"content": message, "memory_type": "goal", "importance": 8},
                ),
                BrainAction(action="update_journal", params={"message": message}),
            ]
        )

    elif context.classification.get("should_save_memory"):
        actions.append(BrainAction(action="update_journal", params={"message": message}))

    if not actions:
        actions.append(BrainAction(action="none"))

    return actions
