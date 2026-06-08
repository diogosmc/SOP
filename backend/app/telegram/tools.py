"""Instructor tools delegating to existing services."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.classifier import classify_message
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService
from app.modules.memory.service import MemoryService
from app.modules.notes.schemas import NoteCreate
from app.modules.notes.service import NoteService
from app.modules.tasks.schemas import TaskCreate
from app.modules.tasks.service import TaskService
from app.telegram.formatter import format_telegram_reply

ChatServiceFactory = Callable[[AsyncSession], ChatService]


def _extract_task_title(message: str) -> str:
    lowered = message.lower().strip()
    prefixes = (
        "preciso fazer ",
        "tenho que ",
        "lembrar de ",
        "criar tarefa ",
        "nova tarefa ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return message[len(prefix) :].strip(" .")[:500]
    return message.strip()[:500]


async def handle_memory_intent(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    classification: dict[str, Any],
) -> None:
    """Persist memories and journal entries via MemoryService."""
    if not classification.get("should_save_memory") and classification.get("intent") not in {
        "study_log",
        "workout_log",
        "expense_log",
        "emotional_checkin",
        "goal_update",
        "habit_log",
    }:
        return
    await MemoryService(db).process_chat_message(user_id, message)


async def handle_journal_intent(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    classification: dict[str, Any],
) -> None:
    """Journal updates are handled inside MemoryService.process_chat_message."""
    await handle_memory_intent(db, user_id, message, classification)


async def handle_task_intent(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    classification: dict[str, Any],
) -> str:
    """Create a simple pending task from natural language."""
    title = _extract_task_title(message)
    if not title:
        return format_telegram_reply("Não consegui identificar o título da tarefa.")

    task = await TaskService(db).create(user_id, TaskCreate(title=title))
    return format_telegram_reply(
        f"Tarefa criada: «{task.title}». Você pode gerenciá-la pelo dashboard em breve."
    )


async def handle_note_intent(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    classification: dict[str, Any],
) -> str:
    """Create a simple note for study-related messages."""
    title = "Registro de estudo"
    lowered = message.lower()
    if "python" in lowered:
        title = "Estudo: Python"
    elif "estudei" in lowered:
        title = message[:80].strip(" .") or title

    note = await NoteService(db).create(
        user_id,
        NoteCreate(title=title, content=message, tags=["estudo", "telegram"]),
    )
    return format_telegram_reply(
        f"Anotado nos estudos: «{note.title}». Salvei também na memória e no diário."
    )


async def handle_chat_fallback(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    chat_service_factory: Optional[ChatServiceFactory] = None,
) -> str:
    """Fallback to the existing chat service when no structured action applies."""
    factory = chat_service_factory or (lambda session: ChatService(session))
    service = factory(db)
    result = await service.send_message(
        user_id,
        ChatMessageRequest(message=message, origin="telegram"),
    )
    return format_telegram_reply(result.response)


async def route_instructor_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    *,
    chat_service_factory: Optional[ChatServiceFactory] = None,
    classify_func: Callable[[str], dict[str, Any]] | None = None,
    skip_llm: bool = False,
) -> str:
    """Classify and route a free-form Instructor message via the Jarvis pipeline."""
    from app.telegram.instructor import process_telegram_message

    return await process_telegram_message(
        db,
        user_id,
        message,
        classify_func=classify_func,
        skip_llm=skip_llm or chat_service_factory is not None,
    )
