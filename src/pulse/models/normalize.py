"""Normalizer registry — maps exchange data to canonical models."""

from __future__ import annotations

from typing import Any

from pulse.models.common import (
    CANONICAL_TYPES,
    Candle,
    MarketStats,
    Orderbook,
    Trade,
)


class Normalizer:
    """Registry of exchange-specific normalizers."""

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, Any]] = {}

    def register(self, exchange: str, data_type: str, fn: Any) -> None:
        self._registry.setdefault(exchange, {})[data_type] = fn

    def normalize(self, exchange: str, data_type: str, raw: dict[str, Any]) -> Any:
        fn = self._registry.get(exchange, {}).get(data_type)
        if not fn:
            raise ValueError(f"No normalizer for {exchange}.{data_type}")
        return fn(raw)


normalizer = Normalizer()
