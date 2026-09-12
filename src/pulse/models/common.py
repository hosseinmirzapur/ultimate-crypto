"""Canonical market data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OrderbookLevel(BaseModel):
    price: float
    quantity: float


class Orderbook(BaseModel):
    symbol: str
    exchange: str
    timestamp: datetime
    bids: list[OrderbookLevel]
    asks: list[OrderbookLevel]
    spread: float | None = None
    mid_price: float | None = None


class Trade(BaseModel):
    symbol: str
    exchange: str
    timestamp: datetime
    price: float
    quantity: float
    side: str  # buy / sell
    trade_id: str | None = None


class Candle(BaseModel):
    symbol: str
    exchange: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    resolution: str


class MarketStats(BaseModel):
    symbol: str
    exchange: str
    timestamp: datetime
    last_price: float
    day_high: float
    day_low: float
    day_open: float
    volume_24h: float
    quote_volume_24h: float
    change_24h_pct: float | None = None


CANONICAL_TYPES = {
    "orderbook": Orderbook,
    "trade": Trade,
    "candle": Candle,
    "market_stats": MarketStats,
}
