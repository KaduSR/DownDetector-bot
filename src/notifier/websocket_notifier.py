"""WebSocket notification service for real-time updates."""

from typing import List, Set, Optional
import socketio

from src.models import ChangeEvent
from src.utils.logger import get_logger


class WebSocketNotifier:
    """Handles WebSocket notifications for real-time updates."""

    def __init__(self):
        """Initialize WebSocket notifier."""
        self.logger = get_logger("websocket_notifier")
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
        self.connected_clients: Set[str] = set()

        # Register event handlers
        self.sio.on("connect", self._handle_connect)
        self.sio.on("disconnect", self._handle_disconnect)
        self.sio.on("subscribe", self._handle_subscribe)

    async def _handle_connect(self, sid: str, environ: dict) -> None:
        """Handle client connection."""
        self.connected_clients.add(sid)
        self.logger.info(f"Client connected: {sid}")
        await self.sio.emit("connection_established", {"sid": sid}, room=sid)

    async def _handle_disconnect(self, sid: str) -> None:
        """Handle client disconnection."""
        self.connected_clients.discard(sid)
        self.logger.info(f"Client disconnected: {sid}")

    async def _handle_subscribe(self, sid: str, data: dict) -> None:
        """Handle client subscription requests."""
        # Future: Handle service-specific subscriptions
        self.logger.debug(f"Subscription request from {sid}: {data}")
        await self.sio.emit("subscribed", {"status": "ok"}, room=sid)

    async def broadcast_changes(self, changes: List[ChangeEvent]) -> None:
        """
        Broadcast changes to all connected clients.

        Args:
            changes: List of change events
        """
        if not changes:
            return

        if not self.connected_clients:
            self.logger.debug("No connected clients to broadcast to")
            return

        # Convert changes to dict format
        change_data = [change.to_dict() for change in changes]

        # Broadcast to all connected clients
        await self.sio.emit("outage_update", {
            "changes": change_data,
            "count": len(changes),
        })

        self.logger.info(f"Broadcast {len(changes)} changes to {len(self.connected_clients)} clients")

    async def send_to_client(self, sid: str, event: str, data: dict) -> None:
        """
        Send event to a specific client.

        Args:
            sid: Client session ID
            event: Event name
            data: Event data
        """
        if sid in self.connected_clients:
            await self.sio.emit(event, data, room=sid)

    def get_asgi_app(self) -> socketio.ASGIApp:
        """Get ASGI app for integration with FastAPI."""
        return socketio.ASGIApp(self.sio)

    def get_connected_count(self) -> int:
        """Get number of connected clients."""
        return len(self.connected_clients)

    async def close(self) -> None:
        """Close all connections."""
        for sid in list(self.connected_clients):
            await self.sio.disconnect(sid)
        self.connected_clients.clear()
        self.logger.info("WebSocket notifier closed")
