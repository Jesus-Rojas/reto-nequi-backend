from fastapi import WebSocket

SessionId = str


class WebSocketManager:
    """Tracks active WebSocket connections grouped by session_id."""

    def __init__(self):
        self._connections: dict[SessionId, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: SessionId) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: SessionId) -> None:
        session_clients = self._connections.get(session_id, [])
        if websocket in session_clients:
            session_clients.remove(websocket)
        if not session_clients:
            self._connections.pop(session_id, None)

    async def broadcast_to_session(
        self, session_id: SessionId, payload: dict
    ) -> None:
        """Send a JSON payload to all clients listening on *session_id*."""
        for websocket in list(self._connections.get(session_id, [])):
            try:
                await websocket.send_json(payload)
            except Exception:
                # Silently drop dead connections; cleanup happens on disconnect
                self.disconnect(websocket, session_id)


# Singleton instance shared across the application
manager = WebSocketManager()
