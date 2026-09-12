"""Signal engine — aggregates exchange data, runs strategies, emits signals."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SignalEngine:
    def __init__(self, strategies: list[Any], event_bus: Any) -> None:
        self.strategies = strategies
        self.event_bus = event_bus

    async def process(self, data: dict[str, Any]) -> None:
        for strategy in self.strategies:
            signal = await strategy.on_signal(data)
            if signal:
                logger.info("Signal: %s", signal)
                await self.event_bus.emit("signal", signal)
