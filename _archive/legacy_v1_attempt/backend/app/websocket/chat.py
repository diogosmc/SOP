"""WebSocket chat streaming."""

import uuid
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaClient
from app.ai.router import select_model
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.modules.chat.models import ChatMode, MessageRole
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import ChatMessageRequest


async def _resolve_user_id(websocket: WebSocket) -> uuid.UUID:
    settings = get_settings()
    user_id = getattr(websocket.state, "user_id", None)
    if user_id:
        return uuid.UUID(str(user_id))
    if settings.single_user_mode:
        return uuid.UUID(settings.default_user_id)
    await websocket.close(code=4401, reason="Not authenticated")
    raise WebSocketDisconnect()


async def handle_chat_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    user_id = await _resolve_user_id(websocket)
    ollama = OllamaClient()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json({"type": "error", "content": "Message is required"})
                continue

            session_id_raw = data.get("session_id")
            mode_raw = data.get("mode")

            async with AsyncSessionLocal() as db:
                try:
                    await _stream_response(
                        websocket,
                        db,
                        ollama,
                        user_id,
                        message,
                        session_id_raw,
                        mode_raw,
                    )
                    await db.commit()
                except Exception as exc:
                    await db.rollback()
                    await websocket.send_json({"type": "error", "content": str(exc)})
    except WebSocketDisconnect:
        pass


async def _stream_response(
    websocket: WebSocket,
    db: AsyncSession,
    ollama: OllamaClient,
    user_id: uuid.UUID,
    message: str,
    session_id_raw: Optional[str],
    mode_raw: Optional[str],
) -> None:
    repo = ChatRepository(db)
    mode = ChatMode(mode_raw) if mode_raw else None

    request = ChatMessageRequest(
        message=message,
        session_id=uuid.UUID(session_id_raw) if session_id_raw else None,
        mode=mode,
    )

    if request.session_id:
        session = await repo.get_session(request.session_id, user_id)
        if not session:
            await websocket.send_json({"type": "error", "content": "Session not found"})
            return
    else:
        session = await repo.create_session(user_id, mode=request.mode or ChatMode.GENERAL)

    await repo.create_message(session.id, user_id, MessageRole.USER, message)

    history = await repo.list_messages(session.id, user_id)
    model = select_model(mode=session.mode, message=message)
    ollama_messages = [{"role": msg.role.value, "content": msg.content} for msg in history]

    full_response = ""
    async for token in ollama.stream_chat(model, ollama_messages):
        full_response += token
        await websocket.send_json({"type": "token", "content": token})

    await repo.create_message(
        session.id, user_id, MessageRole.ASSISTANT, full_response, model=model
    )

    title = session.title
    if not title:
        title = message[:80] + ("..." if len(message) > 80 else "")

    await repo.update_session(
        session,
        title=title,
        model_used=model,
        increment_messages=2,
    )

    await websocket.send_json({"type": "done", "content": full_response})
