"""Signals REST + WebSocket endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class SignalResponse(BaseModel):
    id: str
    symbol: str
    exchange: str
    signal_type: str
    strength: str
    confidence: float
    direction: str
    timestamp: str
    details: str | None = None


@router.get("/latest")
async def latest_signals() -> dict[str, Any]:
    """Latest active signals."""
    return {"signals": []}


@router.get("/history")
async def signal_history(symbol: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Historical signals."""
    return {"signals": []}


@router.websocket("/live")
async def live_signals(ws: WebSocket) -> None:
    """WebSocket stream of live signals."""
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_json({"type": "ack", "received": json.loads(data)})
    except Exception:
        pass
    finally:
        await ws.close()
