"""Tests for chat API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


MOCK_OLLAMA_RESPONSE = {
    "message": {"role": "assistant", "content": "Aqui está sua resposta."}
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_chat_message_creates_session(client: AsyncClient) -> None:
    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(return_value=MOCK_OLLAMA_RESPONSE),
    ):
        response = await client.post(
            "/api/v1/chat/message",
            json={"message": "me ajude a organizar meu dia", "origin": "api"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["session_id"]
    assert data["message"] == "me ajude a organizar meu dia"
    assert data["response"] == "Aqui está sua resposta."
    assert data["model_used"]
    assert isinstance(data["response_time_ms"], int)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_chat_message_reuses_session(client: AsyncClient) -> None:
    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(return_value=MOCK_OLLAMA_RESPONSE),
    ):
        first = await client.post(
            "/api/v1/chat/message",
            json={"message": "primeira", "origin": "api"},
        )
        session_id = first.json()["data"]["session_id"]

        second = await client.post(
            "/api/v1/chat/message",
            json={
                "message": "segunda",
                "session_id": session_id,
                "origin": "api",
            },
        )

    assert second.status_code == 200
    assert second.json()["data"]["session_id"] == session_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient) -> None:
    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(return_value=MOCK_OLLAMA_RESPONSE),
    ):
        await client.post(
            "/api/v1/chat/message",
            json={"message": "listar sessões", "origin": "api"},
        )

    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert len(body["data"]["items"]) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_session_messages(client: AsyncClient) -> None:
    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(return_value=MOCK_OLLAMA_RESPONSE),
    ):
        created = await client.post(
            "/api/v1/chat/message",
            json={"message": "histórico", "origin": "api"},
        )
        session_id = created.json()["data"]["session_id"]

    response = await client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert response.status_code == 200
    messages = response.json()["data"]["items"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient) -> None:
    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(return_value=MOCK_OLLAMA_RESPONSE),
    ):
        created = await client.post(
            "/api/v1/chat/message",
            json={"message": "deletar sessão", "origin": "api"},
        )
        session_id = created.json()["data"]["session_id"]

    delete_resp = await client.delete(f"/api/v1/chat/sessions/{session_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    messages_resp = await client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert messages_resp.status_code == 404
    body = messages_resp.json()
    assert body["success"] is False
    assert "message" in body["error"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_offline_controlled_error(client: AsyncClient) -> None:
    from app.ai.ollama import OllamaError

    with patch(
        "app.modules.chat.service.ollama_chat",
        new=AsyncMock(side_effect=OllamaError("connection refused")),
    ):
        response = await client.post(
            "/api/v1/chat/message",
            json={"message": "teste offline", "origin": "api"},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert "Ollama" in body["error"]["message"]
