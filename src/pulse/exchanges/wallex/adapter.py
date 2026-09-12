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
        self.stream_key = config.get("stream_key")
        self.ws_url = config.get("ws_url", self._ws_url)
        self.rest_url = config.get("rest_url", self._base_url)
        self.symbols = config.get("symbols", [])
        self.proxy = config.get("proxy")
        self.event_bus = event_bus
        self._connected = False
        self._ws: Any = None

    def _sign(self, timestamp: str) -> str:
        """Wallex HMAC-SHA256 signature for REST auth."""
        message = f"{timestamp}{self.api_key}"
        return hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    async def _auth_headers(self) -> dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        return {
            "x-api-key": self.api_key,
            "x-signature": self._sign(timestamp),
            "x-timestamp": timestamp,
            "Content-Type": "application/json",
        }

    async def connect(self) -> None:
        logger.info("Wallex: connecting")
        if self.api_key and self.api_secret:
            try:
                async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
                    headers = await self._auth_headers()
                    resp = await client.post(
                        f"{self.rest_url}/api/v1/auth/login",
                        headers=headers,
                        json={"api_key": self.api_key},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        self.stream_key = data.get("stream_key") or self.stream_key
                        logger.info("Wallex: authenticated, stream_key=%s", bool(self.stream_key))
            except Exception as exc:
                logger.warning("Wallex auth failed: %s", exc)
        self._connected = True
        logger.info("Wallex: connected")

    async def disconnect(self) -> None:
        self._connected = False
        if self._ws:
            await self._ws.close()
        logger.info("Wallex: disconnected")

    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to WS channels. Format: MARKET@buyDepth, MARKET@sellDepth, MARKET@trade, all@price."""
        if not self._connected:
            await self.connect()
        # Wallex expects JSON array: ["subscribe", {"channel": "..."}]
        for ch in channels:
            msg = json.dumps({"id": int(time.time() * 1000), "type": "subscribe", "channel": ch})
            logger.info("Wallex: subscribe %s", ch)
            if self._ws:
                await self._ws.send(msg)

    def parse_message(self, raw: str | bytes) -> dict[str, Any]:
        return json.loads(raw)

    def normalize(self, data: dict[str, Any], data_type: str) -> dict[str, Any]:
        if data_type == "orderbook_buy":
            return self._normalize_orderbook_side(data, "buy")
        if data_type == "orderbook_sell":
            return self._normalize_orderbook_side(data, "sell")
        if data_type == "trade":
            return self._normalize_trade(data)
        if data_type == "ticker":
            return self._normalize_ticker(data)
        if data_type == "candle":
            return self._normalize_candle(data)
        return data

    def _normalize_orderbook_side(self, data: dict[str, Any], side: str) -> dict[str, Any]:
        symbol = data.get("symbol", "")
        levels_raw = data.get("data", [])
        levels = []
        for level in levels_raw:
            levels.append({
                "price": float(level.get("price", 0)),
                "quantity": float(level.get("quantity", 0)),
                "sum": float(level.get("sum", 0)),
            })
        return {
            "symbol": symbol,
            "exchange": self.name,
            "timestamp": datetime.now(timezone.utc),
            "side": side,
            "levels": levels,
        }

    def _normalize_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        symbol = data.get("symbol", "")
        return {
            "symbol": symbol,
            "exchange": self.name,
            "timestamp": datetime.fromtimestamp(data.get("timestamp", 0) / 1000, tz=timezone.utc),
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
            "change_24h_pct": float(data.get("24h_ch", 0)),
        }

    def _normalize_candle(self, data: dict[str, Any]) -> dict[str, Any]:
        # UDF format: {s, t[], o[], h[], l[], c[], v[]}
        return {
            "symbol": data.get("symbol", ""),
            "exchange": self.name,
            "timestamps": data.get("t", []),
            "open": data.get("o", []),
            "high": data.get("h", []),
            "low": data.get("l", []),
            "close": data.get("c", []),
            "volume": data.get("v", []),
            "status": data.get("s", "ok"),
        }

    async def fetch_candles(self, symbol: str, resolution: str = "60", from_ts: int | None = None, to_ts: int | None = None) -> dict[str, Any]:
        """Fetch OHLC candles via REST."""
        params: dict[str, Any] = {"symbol": symbol, "resolution": resolution}
        if from_ts:
            params["from"] = str(from_ts)
        if to_ts:
            params["to"] = str(to_ts)
        async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
            resp = await client.get(f"{self.rest_url}/v1/udf/history", params=params)
            resp.raise_for_status()
            return resp.json()

    async def fetch_depth(self, symbol: str) -> dict[str, Any]:
        """Fetch orderbook depth via REST."""
        async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
            resp = await client.get(f"{self.rest_url}/v1/depth", params={"symbol": symbol})
            resp.raise_for_status()
            return resp.json()

    async def fetch_trades(self, symbol: str) -> dict[str, Any]:
        """Fetch recent trades via REST."""
        async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
            resp = await client.get(f"{self.rest_url}/v1/trades", params={"symbol": symbol})
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=5.0) as client:
                resp = await client.get(f"{self.rest_url}/hector/web/v1/markets")
                resp.raise_for_status()
            return {"exchange": self.name, "status": "ok"}
        except Exception as exc:
            return {"exchange": self.name, "status": "error", "detail": str(exc)}
