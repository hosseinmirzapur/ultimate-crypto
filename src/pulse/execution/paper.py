"""Paper trading engine — simulates fills without real money."""

from __future__ import annotations

import logging
import random
from typing import Any

from pulse.execution.base import ExecutionEngine

logger = logging.getLogger(__name__)


class PaperEngine(ExecutionEngine):
    mode = "paper"

    def __init__(self, slippage_bps: float = 5.0) -> None:
        self.slippage_bps = slippage_bps
        self._positions: dict[str, dict[str, Any]] = {}

    async def submit(self, order: dict[str, Any]) -> dict[str, Any]:
        symbol = order.get("symbol", "UNKNOWN")
        side = order.get("side", "buy")
        qty = order.get("quantity", 0.0)
        price = order.get("price", 0.0)
        slippage = price * (self.slippage_bps / 10000.0) * random.uniform(-1, 1)
        fill_price = price + slippage if side == "buy" else price - slippage
        fill = {
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "price": fill_price,
            "status": "filled",
            "mode": self.mode,
        }
        logger.info("Paper fill: %s", fill)
        return fill

    async def cancel(self, order_id: str) -> None:
        logger.info("Paper cancel: %s", order_id)

    async def positions(self) -> list[dict[str, Any]]:
        return list(self._positions.values())
