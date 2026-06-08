"""Build conversation context for the Brain."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.memory_selector import select_important_memories, select_relevant_memories
from app.brain.schemas import ConversationContext, ConversationState
from app.brain.state_manager import get_or_create_user_state, is_ack_message
from app.core.config import get_settings
from app.modules.chat.models import ChatMessage, ChatSession, MessageRole
from app.modules.memory.models import MemoryType
from app.modules.memory.repository import MemoryRepository
from app.modules.reminders.models import Reminder, ReminderStatus
from app.modules.tasks.models import Task, TaskStatus
from app.brain.classifier import classify_message as classify_telegram_message


def _truncate(text: str, max_len: int = 300) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


async def _recent_messages(
    db: AsyncSession, user_id: uuid.UUID, limit: int
) -> list[dict[str, str]]:
    result = await db.execute(
        select(ChatMessage, ChatSession)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    rows = list(result.all())
    rows.reverse()
    messages: list[dict[str, str]] = []
    for msg, _session in rows:
        messages.append(
            {
                "role": msg.role.value,
                "content": _truncate(msg.content, 500),
            }
        )
    return messages


async def _pending_tasks(db: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[str]:
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user_id, Task.status == TaskStatus.PENDING)
        .order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
        .limit(limit)
    )
    return [_truncate(task.title, 120) for task in result.scalars().all()]


async def _upcoming_reminders(db: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[str]:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=2)
    result = await db.execute(
        select(Reminder)
        .where(
            Reminder.user_id == user_id,
            Reminder.status == ReminderStatus.PENDING,
            Reminder.remind_at >= now,
            Reminder.remind_at <= horizon,
        )
        .order_by(Reminder.remind_at.asc())
        .limit(limit)
    )
    return [_truncate(reminder.title, 120) for reminder in result.scalars().all()]


async def _today_journal_summary(db: AsyncSession, user_id: uuid.UUID) -> str | None:
    from zoneinfo import ZoneInfo

    from app.core.config import get_settings

    tz = ZoneInfo(get_settings().timezone)
    today = datetime.now(tz).date()
    repo = MemoryRepository(db)
    journal = await repo.get_journal_by_date(user_id, today)
    if journal is None:
        return None
    parts: list[str] = []
    if journal.summary:
        parts.append(_truncate(journal.summary, 400))
    if journal.mood_score is not None:
        parts.append(f"Humor: {journal.mood_score}/10")
    if journal.study_summary:
        parts.append(f"Estudo: {_truncate(journal.study_summary, 200)}")
    return " | ".join(parts) if parts else None


async def _primary_goal(db: AsyncSession, user_id: uuid.UUID) -> str | None:
    from app.modules.memory.models import AIMemory

    goal_result = await db.execute(
        select(AIMemory)
        .where(AIMemory.user_id == user_id, AIMemory.type == MemoryType.GOAL)
        .order_by(AIMemory.importance.desc())
        .limit(1)
    )
    goal = goal_result.scalar_one_or_none()
    return _truncate(goal.content, 200) if goal else None


def _estimate_context_chars(context: ConversationContext) -> int:
    total = len(context.message)
    for msg in context.recent_messages:
        total += len(msg.get("content", ""))
    for mem in context.important_memories + context.relevant_memories:
        total += len(mem.content)
    for task in context.pending_tasks:
        total += len(task)
    for reminder in context.upcoming_reminders:
        total += len(reminder)
    if context.today_journal_summary:
        total += len(context.today_journal_summary)
    if context.primary_goal:
        total += len(context.primary_goal)
    return total


def _trim_context(context: ConversationContext, max_chars: int) -> ConversationContext:
    while _estimate_context_chars(context) > max_chars and context.recent_messages:
        context.recent_messages.pop(0)
    while _estimate_context_chars(context) > max_chars and len(context.relevant_memories) > 1:
        context.relevant_memories.pop()
    while _estimate_context_chars(context) > max_chars and len(context.important_memories) > 1:
        context.important_memories.pop()
    context.context_chars = _estimate_context_chars(context)
    return context


async def build_conversation_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
) -> ConversationContext:
    settings = get_settings()
    classification = classify_telegram_message(message)
    intent = classification.get("intent", "general_chat")
    state = await get_or_create_user_state(db, user_id)

    important = await select_important_memories(db, user_id, settings.brain_memory_limit)
    relevant = await select_relevant_memories(db, user_id, message, settings.brain_memory_limit)
    recent = await _recent_messages(db, user_id, settings.brain_recent_messages_limit)

    context = ConversationContext(
        message=message,
        recent_messages=recent,
        state=state,
        important_memories=important,
        relevant_memories=relevant,
        pending_tasks=await _pending_tasks(db, user_id),
        upcoming_reminders=await _upcoming_reminders(db, user_id),
        today_journal_summary=await _today_journal_summary(db, user_id),
        primary_goal=await _primary_goal(db, user_id),
        classification=classification,
        intent=intent,
        is_ack=is_ack_message(message),
    )
    return _trim_context(context, settings.brain_context_max_chars)
