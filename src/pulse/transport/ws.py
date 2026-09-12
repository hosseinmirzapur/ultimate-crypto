"""WebSocket connection manager with auto-reconnect and backoff."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WSConnectionManager:
    """Manages a single WS connection with reconnect/backoff."""

    def __init__(
        self,
        url: str,
        on_message: Callable[[str | bytes], Coroutine[Any, Any, None]],
        ping_interval: float = 20.0,
        ping_timeout: float = 20.0,
        max_reconnect_delay: float = 60.0,
        proxy: str | None = None,
    ) -> None:
        self.url = url
        self.on_message = on_message
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_reconnect_delay = max_reconnect_delay
        self.proxy = proxy
        self._ws: WebSocketClientProtocol | None = None
        self._reconnect_delay = 1.0
        self._connected = False
        self._connect_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        if self._connect_task and not self._connect_task.done():
            return
        self._connect_task = asyncio.create_task(self._connect_loop())

    async def disconnect(self) -> None:
        self._connected = False
        if self._connect_task:
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()

    async def send(self, message: str | bytes) -> None:
        if not self._ws:
            raise RuntimeError("WebSocket not connected")
        await self._ws.send(message)

    @property
    def connected(self) -> bool:
        return self._connected

    async def _connect_loop(self) -> None:
        while True:
            try:
                await self._connect_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("WS connection failed: %s", exc)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self.max_reconnect_delay)

    async def _connect_once(self) -> None:
        extra = {}
        if self.proxy:
            # websockets library uses proxy via `extra_headers` or `proxy` kwarg in newer versions
            extra["proxy"] = self.proxy

        async with websockets.connect(
            self.url,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            **extra,
        ) as ws:
            self._ws = ws
            self._connected = True
            self._reconnect_delay = 1.0
            logger.info("WS connected: %s", self.url)
            async for message in ws:
                await self.on_message(message)
