"""Conversation Brain schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationInput(BaseModel):
    message: str
    origin: str = "telegram"
    prefer_speed: bool = True
    allow_tools: bool = True
    allow_llm: bool = True


class ConversationState(BaseModel):
    mood: str | None = None
    energy: str | None = None
    current_focus: str | None = None
    current_topic: str | None = None
    conversation_mode: str = "normal"
    last_intent: str | None = None
    last_user_message: str | None = None
    last_assistant_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySnippet(BaseModel):
    content: str
    memory_type: str
    importance: int = 5
    category: str = "recent"


class ConversationContext(BaseModel):
    message: str
    recent_messages: list[dict[str, str]] = Field(default_factory=list)
    state: ConversationState = Field(default_factory=ConversationState)
    important_memories: list[MemorySnippet] = Field(default_factory=list)
    relevant_memories: list[MemorySnippet] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    upcoming_reminders: list[str] = Field(default_factory=list)
    today_journal_summary: str | None = None
    primary_goal: str | None = None
    classification: dict[str, Any] = Field(default_factory=dict)
    intent: str = "general_chat"
    is_ack: bool = False
    context_chars: int = 0


class BrainAction(BaseModel):
    action: Literal[
        "create_task",
        "create_reminder",
        "create_note",
        "create_memory",
        "update_journal",
        "create_finance_transaction",
        "create_study_log",
        "create_workout_log",
        "none",
    ]
    params: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None


class BrainResult(BaseModel):
    response: str
    actions: list[BrainAction] = Field(default_factory=list)
    model_used: str | None = None
    response_time_ms: int = 0
    used_llm: bool = False
    used_fallback: bool = False
    intent: str = "general_chat"
    state: dict[str, Any] = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    message: str
    total_ms: int
    first_response_ms: int
    model_used: str | None = None
    used_fallback: bool = False
    used_llm: bool = False
    actions: list[str] = Field(default_factory=list)
    response: str = ""
    status: str = "OK"
    error: str | None = None
