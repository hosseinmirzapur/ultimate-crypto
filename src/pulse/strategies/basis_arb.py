"""Basis arbitrage strategy — spot vs perps spread."""

from __future__ import annotations

import logging
from typing import Any

from pulse.strategies.base import Strategy

logger = logging.getLogger(__name__)


class BasisArbStrategy(Strategy):
    name = "basis_arb"

    def __init__(self, threshold_pct: float = 1.0) -> None:
        self.threshold = threshold_pct

    async def on_signal(self, data: dict[str, Any]) -> dict[str, Any] | None:
        spot = data.get("spot_price")
        perp = data.get("perp_price")
        if spot is None or perp is None:
            return None
        basis_pct = (perp - spot) / spot * 100.0 if spot else 0.0
        if abs(basis_pct) >= self.threshold:
            return {
                "strategy": self.name,
                "symbol": data.get("symbol"),
                "basis_pct": basis_pct,
                "direction": "long_spot_short_perp" if basis_pct > 0 else "short_spot_long_perp",
                "confidence": min(abs(basis_pct) / 5.0, 1.0),
            }
        return None
