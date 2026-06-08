"""Tests for WebSocket chat streaming."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketState

from app.ai.ollama import OllamaError
from app.main import app
from app.websocket.manager import ConnectionManager
from tests.conftest import TestSessionLocal


async def _mock_stream_success(*args, **kwargs) -> AsyncIterator[str]:
    for token in ["Olá", " ", "mundo"]:
        yield token


async def _mock_stream_fail(*args, **kwargs) -> AsyncIterator[str]:
    if False:
        yield ""
    raise OllamaError("stream failed")


@pytest.fixture(scope="module")
def ws_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def ws_client(ws_event_loop) -> TestClient:
    with (
        patch("app.websocket.chat.AsyncSessionLocal", TestSessionLocal),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.dispose_engine", new_callable=AsyncMock),
    ):
        with TestClient(app) as client:
            yield client


def _chat_payload(
    message: str = "organizar meu dia",
    session_id: str | None = None,
) -> dict:
    payload: dict = {
        "type": "chat_message",
        "payload": {
            "message": message,
            "origin": "dashboard",
            "force_fast": False,
            "force_deep": False,
        },
    }
    if session_id:
        payload["payload"]["session_id"] = session_id
    return payload


@pytest.mark.integration
def test_websocket_connection(ws_client: TestClient) -> None:
    with ws_client.websocket_connect("/ws/chat") as ws:
        assert ws is not None


@pytest.mark.integration
def test_websocket_chat_start(ws_client: TestClient) -> None:
    with patch(
        "app.websocket.chat.ollama_stream_chat",
        new=_mock_stream_success,
    ):
        with ws_client.websocket_connect("/ws/chat") as ws:
            ws.send_json(_chat_payload())
            event = ws.receive_json()
            ws.receive_json()
            ws.receive_json()
            ws.receive_json()

    assert event["type"] == "chat_start"
    assert event["payload"]["session_id"]
    assert event["payload"]["model_used"]
    assert event["payload"]["complexity"] in {"simple", "complex"}


@pytest.mark.integration
def test_websocket_receives_tokens(ws_client: TestClient) -> None:
    with patch(
        "app.websocket.chat.ollama_stream_chat",
        new=_mock_stream_success,
    ):
        with ws_client.websocket_connect("/ws/chat") as ws:
            ws.send_json(_chat_payload())
            ws.receive_json()
            tokens = []
            for _ in range(3):
                event = ws.receive_json()
                assert event["type"] == "chat_token"
                tokens.append(event["payload"]["token"])
            done = ws.receive_json()

    assert tokens == ["Olá", " ", "mundo"]
    assert done["type"] == "chat_done"
    assert done["payload"]["response_time_ms"] >= 0


@pytest.mark.integration
def test_websocket_chat_done(ws_client: TestClient) -> None:
    with patch(
        "app.websocket.chat.ollama_stream_chat",
        new=_mock_stream_success,
    ):
        with ws_client.websocket_connect("/ws/chat") as ws:
            ws.send_json(_chat_payload())
            events = [ws.receive_json() for _ in range(5)]

    assert events[-1]["type"] == "chat_done"
    assert events[0]["payload"]["session_id"] == events[-1]["payload"]["session_id"]


@pytest.mark.integration
def test_websocket_persists_conversation(ws_client: TestClient) -> None:
    with patch(
        "app.websocket.chat.ollama_stream_chat",
        new=_mock_stream_success,
    ):
        with ws_client.websocket_connect("/ws/chat") as ws:
            ws.send_json(_chat_payload("persistir conversa"))
            start = ws.receive_json()
            for _ in range(3):
                ws.receive_json()
            ws.receive_json()

    session_id = start["payload"]["session_id"]
    response = ws_client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert response.status_code == 200
    messages = response.json()["data"]["items"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "persistir conversa"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Olá mundo"
    assert messages[1]["model_used"] == start["payload"]["model_used"]


@pytest.mark.integration
def test_websocket_stream_failure_sends_error(ws_client: TestClient) -> None:
    with patch(
        "app.websocket.chat.ollama_stream_chat",
        new=_mock_stream_fail,
    ):
        with ws_client.websocket_connect("/ws/chat") as ws:
            ws.send_json(_chat_payload("vai falhar"))
            ws.receive_json()
            error = ws.receive_json()

    assert error["type"] == "chat_error"
    assert "Ollama" in error["payload"]["message"]


def test_connection_manager_tracks_multiple_connections(ws_event_loop) -> None:
    manager = ConnectionManager()
    assert manager.active_count == 0

    class FakeWebSocket:
        client_state = WebSocketState.CONNECTED

        async def accept(self) -> None:
            return None

        async def send_json(self, data: dict) -> None:
            return None

    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()
    id1 = ws_event_loop.run_until_complete(manager.connect(ws1))  # type: ignore[arg-type]
    id2 = ws_event_loop.run_until_complete(manager.connect(ws2))  # type: ignore[arg-type]
    assert manager.active_count == 2
    manager.disconnect(id1)
    assert manager.active_count == 1
    manager.disconnect(id2)
    assert manager.active_count == 0
