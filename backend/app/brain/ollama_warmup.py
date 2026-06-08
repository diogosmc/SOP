"""Warm up Ollama fast model on startup."""

from __future__ import annotations

import asyncio
import logging

from app.ai.ollama import OllamaError, ollama_generate
from app.core.config import get_settings

logger = logging.getLogger(__name__)

WARMUP_TIMEOUT_SECONDS = 20.0


async def warmup_ollama_fast_model() -> bool:
    """Load qwen3:4b with a short prompt. Returns True on success."""
    settings = get_settings()
    if not settings.telegram_llm_warmup:
        return False

    logger.info("ollama_warmup_started model=%s", settings.ollama_model_fast)
    try:
        await asyncio.wait_for(
            ollama_generate("ok", model=settings.ollama_model_fast),
            timeout=WARMUP_TIMEOUT_SECONDS,
        )
        logger.info("ollama_warmup_done model=%s", settings.ollama_model_fast)
        return True
    except (OllamaError, asyncio.TimeoutError, Exception):
        logger.exception("ollama_warmup_failed model=%s", settings.ollama_model_fast)
        return False
