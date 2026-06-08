"""Tests for Ollama HTTP client."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.ollama import (
    OllamaError,
    check_ollama_health,
    list_models,
    ollama_stream_chat,
)


def _mock_async_client(**methods: AsyncMock) -> MagicMock:
    mock_client = MagicMock()
    for name, method in methods.items():
        setattr(mock_client, name, method)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_check_ollama_health_true() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = _mock_async_client(get=AsyncMock(return_value=mock_response))

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        assert await check_ollama_health() is True


@pytest.mark.asyncio
async def test_check_ollama_health_false_when_offline() -> None:
    mock_client = _mock_async_client(
        get=AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    )

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        assert await check_ollama_health() is False


@pytest.mark.asyncio
async def test_list_models_parsing() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3.2:3b", "size": 123},
            {"name": "mistral:7b-instruct", "size": 456},
        ]
    }

    mock_client = _mock_async_client(get=AsyncMock(return_value=mock_response))

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        models = await list_models()

    assert len(models) == 2
    assert models[0]["name"] == "llama3.2:3b"


@pytest.mark.asyncio
async def test_list_models_raises_clear_error() -> None:
    mock_client = _mock_async_client(
        get=AsyncMock(side_effect=httpx.ConnectError("offline"))
    )

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        with pytest.raises(OllamaError, match="Failed to list Ollama models"):
            await list_models()


@pytest.mark.asyncio
async def test_stream_chat_returns_async_generator() -> None:
    lines = [
        '{"message": {"content": "Hel"}}',
        '{"message": {"content": "lo"}}',
        '{"message": {"content": ""}}',
    ]

    async def fake_aiter_lines() -> AsyncIterator[str]:
        for line in lines:
            yield line

    mock_stream_response = MagicMock()
    mock_stream_response.raise_for_status = MagicMock()
    mock_stream_response.aiter_lines = fake_aiter_lines

    class StreamContext:
        async def __aenter__(self) -> MagicMock:
            return mock_stream_response

        async def __aexit__(self, *args: object) -> None:
            return None

    mock_client = _mock_async_client()
    mock_client.stream = MagicMock(return_value=StreamContext())

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        stream = ollama_stream_chat([{"role": "user", "content": "Hi"}])
        assert hasattr(stream, "__aiter__")
        chunks = [chunk async for chunk in stream]

    assert chunks == ["Hel", "lo"]


@pytest.mark.asyncio
async def test_check_ollama_health_offline_via_api() -> None:
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    mock_client = _mock_async_client(
        get=AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    )

    with patch("app.ai.ollama._build_client", return_value=mock_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/ai/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ollama"] is False
    assert data["models"] == []
    assert "error" in data
