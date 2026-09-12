"""Wallex adapter — REST + WebSocket, Iranian margin + OTC."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from pulse.exchanges.base import ExchangeClient

logger = logging.getLogger(__name__)


class WallexAdapter(ExchangeClient):
    name = "wallex"
    _base_url = "https://api.wallex.ir"
    _ws_url = "wss://api.wallex.ir/ws"

    def __init__(self, config: dict[str, Any], event_bus: Any | None = None) -> None:
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.ws_url = config.get("ws_url", self._ws_url)
        self.rest_url = config.get("rest_url", self._base_url)
        self.symbols = config.get("symbols", [])
        self.proxy = config.get("proxy")
        self.event_bus = event_bus
        self._connected = False

    def _sign(self, timestamp: str) -> str:
        """Wallex HMAC-SHA256 signature."""
        message = f"{timestamp}{self.api_key}"
        return hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    async def connect(self) -> None:
        logger.info("Wallex: connecting")
        self._connected = True
        logger.info("Wallex: connected")

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Wallex: disconnected")

    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to WS channels. Format: MARKET@trade, MARKET@buy-depth, MARKET@sell-depth"""
        logger.info("Wallex: subscribe %s", channels)

    def parse_message(self, raw: str | bytes) -> dict[str, Any]:
        return json.loads(raw)

    def normalize(self, data: dict[str, Any], data_type: str) -> dict[str, Any]:
        if data_type == "orderbook":
            return self._normalize_orderbook(data)
        if data_type == "trade":
            return self._normalize_trade(data)
        if data_type == "ticker":
            return self._normalize_ticker(data)
        return data

    def _normalize_orderbook(self, data: dict[str, Any]) -> dict[str, Any]:
        symbol = data.get("symbol", "")
        return {
            "symbol": symbol,
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
            "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
            "spread": None,
            "mid_price": None,
        }

    def _normalize_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        symbol = data.get("symbol", "")
        return {
            "symbol": symbol,
            "exchange": self.name,
            "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            "price": float(data.get("price", 0)),
            "quantity": float(data.get("quantity", 0)),
            "side": "buy" if data.get("isBuyOrder") else "sell",
            "trade_id": None,
        }

    def _normalize_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": data.get("symbol", ""),
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "last_price": float(data.get("price", 0)),
            "day_high": float(data.get("high", 0)),
            "day_low": float(data.get("low", 0)),
            "day_open": float(data.get("open", 0)),
            "volume_24h": float(data.get("volume", 0)),
            "quote_volume_24h": float(data.get("quoteVolume", 0)),
            "change_24h_pct": data.get("change"),
        }

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=5.0) as client:
                resp = await client.get(f"{self.rest_url}/hector/web/v1/markets")
                resp.raise_for_status()
            return {"exchange": self.name, "status": "ok"}
        except Exception as exc:
            return {"exchange": self.name, "status": "error", "detail": str(exc)}
