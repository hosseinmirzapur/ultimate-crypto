"""Fill models for backtest engine."""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class FillModel:
    def simulate(self, event: dict[str, Any], signal: dict[str, Any]) -> Any | None:
        raise NotImplementedError


class PerfectFill(FillModel):
    """Zero slippage, immediate fill at signal price."""

    def simulate(self, event: dict[str, Any], signal: dict[str, Any]) -> Any | None:
        from pulse.backtest.engine import Fill
        return Fill(
            symbol=signal.get("symbol", ""),
            side=signal.get("direction", "buy"),
            quantity=signal.get("quantity", 0.01),
            price=event.get("price", 0.0),
            timestamp=event.get("timestamp", datetime.now()),
            commission=0.0,
            slippage=0.0,
        )


class RealisticFill(FillModel):
    """Configurable slippage + partial fills."""

    def __init__(self, slippage_bps: float = 10.0, fill_prob: float = 0.95) -> None:
        self.slippage_bps = slippage_bps
        self.fill_prob = fill_prob

    def simulate(self, event: dict[str, Any], signal: dict[str, Any]) -> Any | None:
        from pulse.backtest.engine import Fill
        if random.random() > self.fill_prob:
            logger.debug("Order rejected (fill_prob=%.2f)", self.fill_prob)
            return None
        price = event.get("price", 0.0)
        slippage = price * (self.slippage_bps / 10000.0) * random.uniform(-1, 1)
        direction = signal.get("direction", "buy")
        fill_price = price + slippage if direction.startswith("long") else price - slippage
        return Fill(
            symbol=signal.get("symbol", ""),
            side=direction,
            quantity=signal.get("quantity", 0.01),
            price=fill_price,
            timestamp=event.get("timestamp", datetime.now()),
            commission=price * 0.001,
            slippage=abs(slippage),
        )
