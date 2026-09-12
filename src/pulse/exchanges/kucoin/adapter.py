"""KuCoin adapter — REST + WebSocket, perpetual futures."""

from __future__ import annotations

import hashlib
import hmac
import base64
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from websockets.client import WebSocketClientProtocol

from pulse.exchanges.base import ExchangeClient
from pulse.models.common import Orderbook, Trade, Candle, MarketStats
from pulse.events import EventBus  # will use in real implementation

logger = logging.getLogger(__name__)


class KuCoinAdapter(ExchangeClient):
    name = "kucoin"
    _base_url = "https://api.kucoin.com"
    _ws_url = "wss://ws-api.kucoin.com"

    def __init__(self, config: dict[str, Any], event_bus: Any | None = None) -> None:
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.api_passphrase = config.get("api_passphrase")
        self.ws_url = config.get("ws_url", self._ws_url)
        self.rest_url = config.get("rest_url", self._base_url)
        self.symbols = config.get("symbols", [])
        self.proxy = config.get("proxy")
        self.event_bus = event_bus
        self._ws: WebSocketClientProtocol | None = None
        self._connected = False

    def _sign(self, timestamp: str, method: str, endpoint: str, body: str = "") -> dict[str, str]:
        """KuCoin signature: base64(hmac_sha256(secret, str_to_sign))."""
        str_to_sign = f"{timestamp}{method}{endpoint}{body}"
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode(), str_to_sign.encode(), hashlib.sha256).digest()
        ).decode()
        passphrase = base64.b64encode(
            hmac.new(self.api_secret.encode(), self.api_passphrase.encode(), hashlib.sha256).digest()
        ).decode()
        return {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json",
        }

    async def connect(self) -> None:
        logger.info("KuCoin: connecting")
        self._connected = True
        logger.info("KuCoin: connected")

    async def _get_ws_token(self) -> dict[str, Any]:
        """Get private WS token (public doesn't need it, but good for private channels)."""
        timestamp = str(int(time.time() * 1000))
        endpoint = "/api/v1/bullet-public"
        headers = self._sign(timestamp, "POST", endpoint)
        async with httpx.AsyncClient(proxy=self.proxy) as client:
            resp = await client.post(
                f"{self.rest_url}{endpoint}",
                headers=headers,
                json={},
            )
            resp.raise_for_status()
            return resp.json()["data"]

    async def disconnect(self) -> None:
        self._connected = False
        if self._ws:
            await self._ws.close()
        logger.info("KuCoin: disconnected")

    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to WS channels. Format: /market/ticker:ETH-USDT-PERP"""
        if not self._connected:
            await self.connect()
        sub_msg = {
            "id": int(time.time() * 1000),
            "type": "subscribe",
            "topic": channels[0] if len(channels) == 1 else None,
            "privateChannel": False,
            "response": True,
        }
        logger.info("KuCoin: subscribe %s", sub_msg)

    def parse_message(self, raw: str | bytes) -> dict[str, Any]:
        """Parse KuCoin WS message."""
        msg = json.loads(raw)
        return msg

    def normalize(self, data: dict[str, Any], data_type: str) -> dict[str, Any]:
        """Map KuCoin fields to canonical schema."""
        if data_type == "orderbook":
            return self._normalize_orderbook(data)
        if data_type == "trade":
            return self._normalize_trade(data)
        if data_type == "candle":
            return self._normalize_candle(data)
        if data_type == "ticker":
            return self._normalize_ticker(data)
        return data

    def _normalize_orderbook(self, data: dict[str, Any]) -> dict[str, Any]:
        asks = [[float(p), float(q)] for p, q in data.get("asks", [])]
        bids = [[float(p), float(q)] for p, q in data.get("bids", [])]
        return {
            "symbol": data.get("symbol", ""),
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "asks": asks,
            "bids": bids,
            "spread": None,
            "mid_price": None,
        }

    def _normalize_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": data.get("symbol", ""),
            "exchange": self.name,
            "timestamp": datetime.fromtimestamp(data.get("time", 0) / 1000, tz=timezone.utc),
            "price": float(data.get("price", 0)),
            "quantity": float(data.get("size", 0)),
            "side": data.get("side", ""),
            "trade_id": str(data.get("tradeId", "")),
        }

    def _normalize_candle(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": data.get("symbol", ""),
            "exchange": self.name,
            "timestamp": datetime.fromtimestamp(data.get("candles", [0])[0] / 1000, tz=timezone.utc),
            "open": float(data.get("candles", [0, 0, 0, 0])[1]),
            "high": float(data.get("candles", [0, 0, 0, 0])[2]),
            "low": float(data.get("candles", [0, 0, 0, 0])[3]),
            "close": float(data.get("candles", [0, 0, 0, 0])[4]),
            "volume": float(data.get("candles", [0, 0, 0, 0, 0])[5]),
            "resolution": data.get("resolution", "1h"),
        }

    def _normalize_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        tick = data.get("data", {})
        return {
            "symbol": data.get("subject", ""),
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "last_price": float(tick.get("price", 0)),
            "day_high": float(tick.get("high", 0)),
            "day_low": float(tick.get("low", 0)),
            "day_open": float(tick.get("open", 0)),
            "volume_24h": float(tick.get("vol", 0)),
            "quote_volume_24h": float(tick.get("volValue", 0)),
            "change_24h_pct": None,
        }

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=5.0) as client:
                resp = await client.get(f"{self.rest_url}/api/v1/status")
                resp.raise_for_status()
            return {"exchange": self.name, "status": "ok"}
        except Exception as exc:
            return {"exchange": self.name, "status": "error", "detail": str(exc)}
