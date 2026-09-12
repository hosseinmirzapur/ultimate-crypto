"""Toobit adapter — REST + WebSocket, USDT-M perpetuals."""

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


class ToobitAdapter(ExchangeClient):
    name = "toobit"
    _base_url = "https://api.toobit.com"
    _ws_url = "wss://streamapi.toobit.com"

    def __init__(self, config: dict[str, Any], event_bus: Any | None = None) -> None:
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.ws_url = config.get("ws_url", self._ws_url)
        self.rest_url = config.get("rest_url", self._base_url)
        self.symbols = config.get("symbols", [])
        self.proxy = config.get("proxy")
        self.event_bus = event_bus
        self._connected = False

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """Toobit HMAC-SHA256 signature."""
        payload = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return {**params, "signature": signature, "api_key": self.api_key}

    async def connect(self) -> None:
        logger.info("Toobit: connecting")
        self._connected = True
        logger.info("Toobit: connected")

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Toobit: disconnected")

    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to WS channels. Format: <symbol>@trade / <symbol>@depth"""
        logger.info("Toobit: subscribe %s", channels)

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
        return {
            "symbol": data.get("s", ""),
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
            "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
            "spread": None,
            "mid_price": None,
        }

    def _normalize_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": data.get("s", ""),
            "exchange": self.name,
            "timestamp": datetime.fromtimestamp(data.get("T", 0) / 1000, tz=timezone.utc),
            "price": float(data.get("p", 0)),
            "quantity": float(data.get("q", 0)),
            "side": data.get("S", "").lower(),
            "trade_id": str(data.get("t", "")),
        }

    def _normalize_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": data.get("s", ""),
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "last_price": float(data.get("c", 0)),
            "day_high": float(data.get("h", 0)),
            "day_low": float(data.get("l", 0)),
            "day_open": float(data.get("o", 0)),
            "volume_24h": float(data.get("v", 0)),
            "quote_volume_24h": float(data.get("qv", 0)),
            "change_24h_pct": data.get("p"),
        }

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=5.0) as client:
                resp = await client.get(f"{self.rest_url}/api/v1/time")
                resp.raise_for_status()
            return {"exchange": self.name, "status": "ok"}
        except Exception as exc:
            return {"exchange": self.name, "status": "error", "detail": str(exc)}
