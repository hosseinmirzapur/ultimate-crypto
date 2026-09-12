"""Live execution engine — disabled by default, requires explicit config."""

from __future__ import annotations

import logging
from typing import Any

from pulse.execution.base import ExecutionEngine

logger = logging.getLogger(__name__)


class LiveEngine(ExecutionEngine):
    mode = "live"

    def __init__(self, enabled: bool = False) -> None:
        if enabled:
            logger.warning("Live execution is ENABLED — real funds at risk")
        else:
            logger.info("Live execution disabled (paper mode)")
        self.enabled = enabled

    async def submit(self, order: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Live execution disabled — use paper mode")
        # TODO: route to correct exchange adapter
        raise NotImplementedError("Live execution not yet implemented")

    async def cancel(self, order_id: str) -> None:
        if not self.enabled:
            raise RuntimeError("Live execution disabled")
        raise NotImplementedError

    async def positions(self) -> list[dict[str, Any]]:
        return []
