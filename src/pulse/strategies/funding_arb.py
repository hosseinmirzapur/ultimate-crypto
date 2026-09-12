"""Funding rate arbitrage strategy."""

from __future__ import annotations

import logging
from typing import Any

from pulse.strategies.base import Strategy

logger = logging.getLogger(__name__)


class FundingArbStrategy(Strategy):
    name = "funding_arb"

    def __init__(self, min_funding_pct: float = 0.01) -> None:
        self.min_funding = min_funding_pct

    async def on_signal(self, data: dict[str, Any]) -> dict[str, Any] | None:
        funding = data.get("funding_rate")
        if funding is None:
            return None
        if abs(funding) >= self.min_funding:
            return {
                "strategy": self.name,
                "symbol": data.get("symbol"),
                "funding_rate": funding,
                "direction": "short" if funding > 0 else "long",
                "confidence": min(abs(funding) / 0.1, 1.0),
            }
        return None
