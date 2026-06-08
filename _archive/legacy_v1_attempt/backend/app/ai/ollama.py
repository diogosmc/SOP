"""Async Ollama HTTP client."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, TypedDict

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaError(Exception):
    """Raised when an Ollama API request fails."""


class ChatMessage(TypedDict):
    """Ollama chat message with role and content."""

    role: str
    content: str


class OllamaClient:
    """Thin async wrapper around the Ollama REST API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._settings.ollama_base_url.rstrip("/"),
            timeout=self._settings.ollama_timeout,
        )

    async def health(self) -> bool:
        """Return True when Ollama responds successfully."""
        try:
            async with self._build_client() as client:
                response = await client.get("/")
                response.raise_for_status()
                return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("ollama_health_check_failed", error=str(exc))
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """Return installed models from Ollama."""
        try:
            async with self._build_client() as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                models = payload.get("models", [])
                if not isinstance(models, list):
                    return []
                return models
        except httpx.HTTPError as exc:
            logger.error("ollama_list_models_failed", error=str(exc))
            raise OllamaError("Failed to list Ollama models") from exc

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a completion against Ollama /api/generate."""
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            payload["system"] = system
        if options is not None:
            payload["options"] = options

        try:
            async with self._build_client() as client:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.HTTPError as exc:
            logger.error(
                "ollama_generate_failed",
                model=model,
                error=str(exc),
            )
            raise OllamaError("Failed to generate Ollama completion") from exc

    async def chat(
        self,
        model: str,
        messages: list[ChatMessage],
        *,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a chat completion against Ollama /api/chat."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options is not None:
            payload["options"] = options

        try:
            async with self._build_client() as client:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.HTTPError as exc:
            logger.error(
                "ollama_chat_failed",
                model=model,
                error=str(exc),
            )
            raise OllamaError("Failed to complete Ollama chat") from exc

    async def stream_chat(
        self,
        model: str,
        messages: list[ChatMessage],
        *,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat tokens from Ollama /api/chat."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if options is not None:
            payload["options"] = options

        try:
            async with self._build_client() as client:
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
        except httpx.HTTPError as exc:
            logger.error(
                "ollama_stream_chat_failed",
                model=model,
                error=str(exc),
            )
            raise OllamaError("Failed to stream Ollama chat") from exc

    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
    ) -> list[float]:
        """Return an embedding vector for the given text."""
        embed_model = model or self._settings.ollama_embed_model
        payload: dict[str, Any] = {
            "model": embed_model,
            "prompt": text,
        }

        try:
            async with self._build_client() as client:
                response = await client.post("/api/embeddings", json=payload)
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                embedding = result.get("embedding")
                if not isinstance(embedding, list):
                    raise OllamaError("Ollama embeddings response missing vector")
                return embedding
        except httpx.HTTPError as exc:
            logger.error(
                "ollama_embed_failed",
                model=embed_model,
                error=str(exc),
            )
            raise OllamaError("Failed to create Ollama embedding") from exc
