"""In-process WebSocket fan-out for live dashboard snapshots."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("axceta.hub")


class SnapshotHub:
    """Keeps connected dashboard clients and broadcasts JSON snapshots."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        logger.info("WS client connected (%d total)", len(self._clients))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)
        logger.info("WS client disconnected (%d total)", len(self._clients))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        message = json.dumps(payload)
        async with self._lock:
            clients = list(self._clients)
        stale: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)
