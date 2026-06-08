"""WebSocket connection manager."""

import uuid
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class ConnectionManager:
    """Track active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self._connections[connection_id] = websocket
        return connection_id

    def disconnect(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def send_event(
        self,
        websocket: WebSocket,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if websocket.client_state != WebSocketState.CONNECTED:
            return
        await websocket.send_json({"type": event_type, "payload": payload})
