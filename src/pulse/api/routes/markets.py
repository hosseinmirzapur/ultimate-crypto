"""Markets REST endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from pulse.models.common import Orderbook, Trade, Candle, MarketStats

logger = logging.getLogger(__name__)
router = APIRouter()


class SymbolResponse(BaseModel):
    symbol: str
    exchange: str
    price: float
    change_24h_pct: float | None
    volume_24h: float
    timestamp: datetime


@router.get("/symbols")
async def list_symbols() -> dict[str, Any]:
    """Return all tracked symbols across exchanges."""
    return {"symbols": []}


@router.get("/orderbook/{exchange}/{symbol}")
async def get_orderbook(exchange: str, symbol: str) -> Orderbook | dict[str, str]:
    """Latest orderbook for symbol."""
    return {"error": "not implemented"}


@router.get("/trades/{exchange}/{symbol}")
async def get_trades(exchange: str, symbol: str, limit: int = 50) -> list[Trade]:
    """Recent trades."""
    return []


@router.get("/candles/{exchange}/{symbol}")
async def get_candles(exchange: str, symbol: str, resolution: str = "1h", limit: int = 100) -> list[Candle]:
    """OHLC candles."""
    return []


@router.get("/stats/{exchange}/{symbol}")
async def get_stats(exchange: str, symbol: str) -> MarketStats | dict[str, str]:
    """24h market stats."""
    return {"error": "not implemented"}
