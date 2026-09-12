"""In-process event bus — decouples components without external broker."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine


EventHandler = Callable[[Any], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        self._listeners[event].append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        if handler in self._listeners[event]:
            self._listeners[event].remove(handler)

    async def emit(self, event: str, data: Any = None) -> None:
        for handler in list(self._listeners.get(event, [])):
            try:
                await handler(data)
            except Exception:
                continue
