"""Direct async HTTP client for Ollama."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaError(Exception):
    """Raised when an Ollama API request fails."""


def _get_settings() -> Settings:
    return get_settings()


def _build_client(
    settings: Settings | None = None,
    timeout_seconds: float | None = None,
) -> httpx.AsyncClient:
    cfg = settings or _get_settings()
    return httpx.AsyncClient(
        base_url=cfg.ollama_base_url.rstrip("/"),
        timeout=timeout_seconds if timeout_seconds is not None else cfg.ollama_timeout_seconds,
    )


def _default_options(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = _get_settings()
    options: dict[str, Any] = {"num_ctx": cfg.ollama_context_size}
    if extra:
        options.update(extra)
    return options


def _resolve_model(model: str | None, default: str) -> str:
    return model or default


async def check_ollama_health() -> bool:
    """Return True when Ollama responds to /api/tags."""
    try:
        async with _build_client() as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            return response.status_code == 200
    except httpx.HTTPError as exc:
        logger.warning("ollama_health_check_failed", error=str(exc))
        return False


async def list_models() -> list[dict[str, Any]]:
    """Return installed models from Ollama /api/tags."""
    try:
        async with _build_client() as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            models = payload.get("models", [])
            if not isinstance(models, list):
                return []
            return models
    except httpx.HTTPError as exc:
        logger.error("ollama_list_models_failed", error=str(exc))
        raise OllamaError(f"Failed to list Ollama models: {exc}") from exc


async def ollama_generate(
    prompt: str,
    model: str | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a completion against Ollama /api/generate."""
    cfg = _get_settings()
    payload: dict[str, Any] = {
        "model": _resolve_model(model, cfg.ollama_model_fast),
        "prompt": prompt,
        "stream": False,
        "keep_alive": cfg.ollama_keep_alive,
        "options": _default_options(options),
    }

    try:
        async with _build_client() as client:
            start = time.perf_counter()
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "ollama_generate_complete",
                model=payload["model"],
                response_time_ms=elapsed_ms,
            )
            return result
    except httpx.HTTPError as exc:
        logger.error("ollama_generate_failed", error=str(exc))
        raise OllamaError(f"Failed to generate Ollama completion: {exc}") from exc


async def ollama_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    options: dict[str, Any] | None = None,
    *,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Run a chat completion against Ollama /api/chat."""
    cfg = _get_settings()
    payload: dict[str, Any] = {
        "model": _resolve_model(model, cfg.ollama_model_fast),
        "messages": messages,
        "stream": False,
        "keep_alive": cfg.ollama_keep_alive,
        "options": _default_options(options),
    }

    try:
        async with _build_client(timeout_seconds=timeout_seconds) as client:
            start = time.perf_counter()
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "ollama_chat_complete",
                model=payload["model"],
                response_time_ms=elapsed_ms,
            )
            return result
    except httpx.HTTPError as exc:
        logger.error("ollama_chat_failed", error=str(exc))
        raise OllamaError(f"Failed to complete Ollama chat: {exc}") from exc


async def ollama_stream_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    options: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    """Stream chat tokens from Ollama /api/chat."""
    cfg = _get_settings()
    payload: dict[str, Any] = {
        "model": _resolve_model(model, cfg.ollama_model_fast),
        "messages": messages,
        "stream": True,
        "keep_alive": cfg.ollama_keep_alive,
        "options": _default_options(options),
    }

    try:
        async with _build_client() as client:
            start = time.perf_counter()
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk: dict[str, Any] = json.loads(line)
                    message = chunk.get("message")
                    if not isinstance(message, dict):
                        continue
                    content = message.get("content")
                    if isinstance(content, str) and content:
                        yield content
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "ollama_stream_chat_complete",
                model=payload["model"],
                response_time_ms=elapsed_ms,
            )
    except httpx.HTTPError as exc:
        logger.error("ollama_stream_chat_failed", error=str(exc))
        raise OllamaError(f"Failed to stream Ollama chat: {exc}") from exc


async def ollama_embed(text: str, model: str | None = None) -> list[float]:
    """Return an embedding vector for the given text via /api/embeddings."""
    cfg = _get_settings()
    payload: dict[str, Any] = {
        "model": _resolve_model(model, cfg.ollama_model_embed),
        "prompt": text,
        "keep_alive": cfg.ollama_keep_alive,
    }

    try:
        async with _build_client() as client:
            start = time.perf_counter()
            response = await client.post("/api/embeddings", json=payload)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "ollama_embed_complete",
                model=payload["model"],
                response_time_ms=elapsed_ms,
            )
            embedding = result.get("embedding")
            if not isinstance(embedding, list):
                raise OllamaError("Ollama embeddings response missing vector")
            return embedding
    except httpx.HTTPError as exc:
        logger.error("ollama_embed_failed", error=str(exc))
        raise OllamaError(f"Failed to create Ollama embedding: {exc}") from exc
