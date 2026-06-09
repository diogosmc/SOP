"""Conversation Brain orchestrator."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.action_executor import execute_actions
from app.brain.background_collector import collect_conversation_data
from app.brain.context_builder import build_conversation_context
from app.brain.response_generator import generate_response
from app.brain.schemas import BrainResult
from app.brain.state_manager import update_state_from_message, update_state_from_response
from app.brain.tool_router import decide_actions
from app.modules.chat.models import ChatOrigin
from app.modules.chat.repository import ChatRepository
from app.modules.chat.models import MessageRole
from app.modules.users.service import ensure_default_user_exists
from app.telegram.formatter import format_telegram_reply

logger = logging.getLogger(__name__)

_LAST_RESORT = (
    "Tô aqui com você. Me conta como você tá — pode ser sobre o dia ou o que tiver pesando."
)

_TELEGRAM_ORIGINS = frozenset({"telegram", "benchmark"})


async def _persist_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    response: str,
    origin: str,
) -> None:
    try:
        repo = ChatRepository(db)
        chat_origin = ChatOrigin.TELEGRAM if origin == "telegram" else ChatOrigin.API
        sessions, _ = await repo.list_sessions(user_id, offset=0, limit=1)
        session = sessions[0] if sessions else await repo.create_session(
            user_id, chat_origin, title=message[:80]
        )
        await repo.create_message(session.id, MessageRole.USER, message)
        await repo.create_message(session.id, MessageRole.ASSISTANT, response)
    except Exception:
        logger.exception("brain_persist_conversation_failed user_id=%s", user_id)


async def process_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    *,
    origin: str = "telegram",
    prefer_speed: bool = True,
    allow_tools: bool = True,
    allow_llm: bool = True,
    response_mode: str | None = None,
    ollama_chat_func: Callable[..., Any] | None = None,
) -> BrainResult:
    started = time.perf_counter()
    await ensure_default_user_exists(db)
    normalized = message.strip()
    if not normalized:
        return BrainResult(
            response="Manda sua mensagem quando quiser.",
            used_fallback=True,
            response_time_ms=0,
        )

    try:
        context = await build_conversation_context(db, user_id, normalized, origin=origin)
        logger.info(
            "brain_context_built user_id=%s intent=%s chars=%s",
            user_id,
            context.intent,
            context.context_chars,
        )

        await update_state_from_message(
            db,
            user_id,
            normalized,
            context.intent,
            context.classification,
        )

        actions: list = []
        companion_first = origin in _TELEGRAM_ORIGINS

        if companion_first:
            # Companion AI responds first; background collector runs after.
            response, model_used, used_fallback = await generate_response(
                normalized,
                context,
                [],
                prefer_speed=prefer_speed,
                allow_llm=allow_llm,
                response_mode=response_mode,
                ollama_chat_func=ollama_chat_func,
            )
            if allow_tools:
                actions = await collect_conversation_data(db, user_id, normalized, context)
        else:
            if allow_tools:
                actions = decide_actions(normalized, context)
                actions = await execute_actions(db, user_id, actions, context.classification)
            response, model_used, used_fallback = await generate_response(
                normalized,
                context,
                actions,
                prefer_speed=prefer_speed,
                allow_llm=allow_llm,
                response_mode=response_mode,
                ollama_chat_func=ollama_chat_func,
            )

        logger.info(
            "brain_response_generated user_id=%s model=%s fallback=%s",
            user_id,
            model_used,
            used_fallback,
        )

        state = await update_state_from_response(db, user_id, response)
        await _persist_conversation(db, user_id, normalized, response, origin)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return BrainResult(
            response=format_telegram_reply(response),
            actions=actions,
            model_used=model_used,
            response_time_ms=elapsed_ms,
            used_llm=model_used is not None,
            used_fallback=used_fallback,
            intent=context.intent,
            state=state.model_dump(),
        )
    except Exception:
        logger.exception("brain_process_message_failed user_id=%s", user_id)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return BrainResult(
            response=format_telegram_reply(_LAST_RESORT),
            used_fallback=True,
            response_time_ms=elapsed_ms,
            intent="general_chat",
        )
