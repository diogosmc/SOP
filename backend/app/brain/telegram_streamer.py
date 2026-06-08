"""Simulated streaming for Telegram via message edits."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.brain.schemas import BrainResult
from app.core.config import get_settings
from app.telegram.formatter import format_telegram_reply

logger = logging.getLogger(__name__)

THINKING_PLACEHOLDER = "💭 Pensando..."


async def _stream_tokens(
    message: str,
    context: Any,
    actions: list,
    *,
    ollama_stream_func: Callable[..., AsyncIterator[str]] | None = None,
) -> AsyncIterator[str]:
    from app.ai.ollama import ollama_stream_chat
    from app.brain.response_generator import _build_system_prompt, _needs_deep_model

    settings = get_settings()
    use_deep = _needs_deep_model(message)
    model = (
        settings.ollama_model_main
        if use_deep and not settings.telegram_force_fast_model
        else settings.ollama_model_fast
    )
    stream_fn = ollama_stream_func or ollama_stream_chat
    messages = [
        {"role": "system", "content": _build_system_prompt(context)},
        {"role": "user", "content": message},
    ]
    async for token in stream_fn(messages, model=model):
        yield token


async def stream_telegram_response(
    telegram_message: Any,
    brain_result_factory: Callable[[], Any],
    *,
    use_streaming_llm: bool = False,
) -> BrainResult:
    """Send/edit Telegram message with block-based streaming."""
    settings = get_settings()
    sent = await telegram_message.reply_text(format_telegram_reply(THINKING_PLACEHOLDER))
    first_response_ms = int((time.perf_counter()) * 1000)
    start = time.perf_counter()

    if not settings.telegram_streaming_enabled:
        result: BrainResult = await brain_result_factory()
        try:
            await sent.edit_text(format_telegram_reply(result.response))
        except Exception:
            logger.exception("telegram_stream_edit_failed")
            await telegram_message.reply_text(format_telegram_reply(result.response))
        result.response_time_ms = int((time.perf_counter() - start) * 1000)
        return result

    accumulated = ""
    last_edit = time.perf_counter()
    result: BrainResult | None = None

    try:
        if use_streaming_llm:
            factory_result = await brain_result_factory()
            accumulated = factory_result.response
            result = factory_result
        else:
            result = await brain_result_factory()
            accumulated = result.response
            min_chars = settings.telegram_stream_min_chars
            interval = settings.telegram_stream_edit_interval_ms / 1000.0
            partial = ""
            for idx, char in enumerate(accumulated):
                partial += char
                now = time.perf_counter()
                if (idx + 1) >= min_chars and (now - last_edit) >= interval:
                    try:
                        await sent.edit_text(format_telegram_reply(partial + " ▌"))
                        last_edit = now
                    except Exception:
                        logger.debug("telegram_stream_edit_skipped")
                    await asyncio.sleep(0.05)
    except Exception:
        logger.exception("telegram_streaming_failed")
        if result is None:
            result = await brain_result_factory()

    try:
        await sent.edit_text(format_telegram_reply(result.response))
    except Exception:
        logger.exception("telegram_stream_final_edit_failed")
        await telegram_message.reply_text(format_telegram_reply(result.response))

    result.response_time_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "telegram_reply_sent streaming=true ms=%s first_ms=%s",
        result.response_time_ms,
        first_response_ms,
    )
    return result
