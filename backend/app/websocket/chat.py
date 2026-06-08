"""WebSocket chat streaming handler."""

import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ai.ollama import OllamaError, ollama_stream_chat
from app.core.config import get_settings
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.db.session import AsyncSessionLocal
from app.modules.chat.models import ChatOrigin
from app.modules.users.service import ensure_default_user_exists
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService, ChatStreamError
from app.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


def _parse_cookie(header: str, name: str) -> Optional[str]:
    for part in header.split(";"):
        part = part.strip()
        if part.startswith(f"{name}="):
            return part.split("=", 1)[1]
    return None


def _resolve_authenticated_user_id(websocket: WebSocket) -> Optional[uuid.UUID]:
    settings = get_settings()
    cookie_header = websocket.headers.get("cookie", "")
    token = _parse_cookie(cookie_header, "access_token")
    if not token:
        return None
    payload = decode_token(token, settings, expected_type=TOKEN_TYPE_ACCESS)
    if payload and payload.get("sub"):
        return uuid.UUID(str(payload["sub"]))
    return None


async def _send_error(websocket: WebSocket, message: str) -> None:
    await manager.send_event(websocket, "chat_error", {"message": message})


def _parse_chat_request(data: dict[str, Any]) -> Optional[ChatMessageRequest]:
    if data.get("type") != "chat_message":
        return None

    payload = data.get("payload")
    if not isinstance(payload, dict):
        return None

    message = str(payload.get("message", "")).strip()
    if not message:
        return None

    session_id = payload.get("session_id")
    origin_raw = payload.get("origin", "dashboard")
    try:
        origin = ChatOrigin(origin_raw)
    except ValueError:
        origin = ChatOrigin.DASHBOARD

    return ChatMessageRequest(
        message=message,
        session_id=uuid.UUID(str(session_id)) if session_id else None,
        origin=origin,
        force_fast=bool(payload.get("force_fast", False)),
        force_deep=bool(payload.get("force_deep", False)),
    )


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    connection_id = await manager.connect(websocket)
    settings = get_settings()

    if settings.auth_enabled:
        user_id = _resolve_authenticated_user_id(websocket)
        if user_id is None:
            await websocket.close(code=4401)
            manager.disconnect(connection_id)
            return
    else:
        async with AsyncSessionLocal() as db:
            user = await ensure_default_user_exists(db)
            user_id = user.id
            await db.commit()

    try:
        while True:
            raw = await websocket.receive_json()
            request = _parse_chat_request(raw)
            if request is None:
                await _send_error(websocket, "Invalid chat_message payload")
                continue

            async with AsyncSessionLocal() as db:
                service = ChatService(db)
                try:
                    await _handle_stream_turn(websocket, service, user_id, request)
                    await db.commit()
                except ChatStreamError as exc:
                    await db.rollback()
                    await _send_error(websocket, exc.message)
                except OllamaError as exc:
                    await db.rollback()
                    await _send_error(websocket, f"Ollama unavailable: {exc}")
                except Exception as exc:
                    await db.rollback()
                    await _send_error(websocket, f"Unexpected error: {exc}")
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(connection_id)


async def _handle_stream_turn(
    websocket: WebSocket,
    service: ChatService,
    user_id: uuid.UUID,
    request: ChatMessageRequest,
) -> None:
    turn = await service.prepare_stream_turn(user_id, request)

    await manager.send_event(
        websocket,
        "chat_start",
        {
            "session_id": str(turn.session_id),
            "model_used": turn.model,
            "complexity": turn.complexity,
        },
    )

    stream_func = service._ollama_stream or ollama_stream_chat
    started = time.perf_counter()
    tokens: list[str] = []

    try:
        async for token in stream_func(turn.ollama_messages, model=turn.model):
            tokens.append(token)
            await manager.send_event(websocket, "chat_token", {"token": token})
    except OllamaError as exc:
        raise OllamaError(str(exc)) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    full_response = "".join(tokens)

    await service.finalize_stream_turn(
        turn.session_id,
        full_response,
        turn.model,
        elapsed_ms,
    )

    await manager.send_event(
        websocket,
        "chat_done",
        {
            "session_id": str(turn.session_id),
            "response_time_ms": elapsed_ms,
        },
    )
