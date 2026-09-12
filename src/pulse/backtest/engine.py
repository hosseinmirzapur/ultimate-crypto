"""Backtest event engine — processes market events through strategy/risk/execution."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class Fill:
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0


@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    avg_entry: float
    timestamp: datetime


class BacktestEngine:
    """Event-driven backtest with realistic fills."""

    def __init__(
        self,
        strategy: Any,
        fill_model: Any,
        initial_capital: float = 100_000.0,
    ) -> None:
        self.strategy = strategy
        self.fill_model = fill_model
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: dict[str, Position] = {}
        self.fills: list[Fill] = []
        self.equity_curve: list[tuple[datetime, float]] = []
        self._event_queue: deque[dict[str, Any]] = deque()
        self._running = False

    def load_events(self, events: list[dict[str, Any]]) -> None:
        self._event_queue = deque(events)

    async def run(self) -> dict[str, Any]:
        self._running = True
        self.equity_curve = [(datetime.now(), self.initial_capital)]
        while self._event_queue and self._running:
            event = self._event_queue.popleft()
            await self._process(event)
            self.equity_curve.append((event.get("timestamp", datetime.now()), self.capital))
        self._running = False
        return {
            "fills": self.fills,
            "equity_curve": self.equity_curve,
            "final_capital": self.capital,
            "total_return_pct": (self.capital - self.initial_capital) / self.initial_capital * 100,
        }

    async def _process(self, event: dict[str, Any]) -> None:
        signal = await self.strategy.on_signal(event)
        if not signal:
            return
        fill = self.fill_model.simulate(event, signal)
        if fill:
            self._apply_fill(fill)

    def _apply_fill(self, fill: Fill) -> None:
        self.fills.append(fill)
        side_mult = 1.0 if fill.side == "buy" else -1.0
        cost = fill.quantity * fill.price + fill.commission
        if side_mult > 0:
            self.capital -= cost
        else:
            self.capital += cost
        pos_key = fill.symbol
        if pos_key in self.positions:
            pos = self.positions[pos_key]
            total_qty = pos.quantity + fill.quantity * side_mult
            if total_qty == 0:
                del self.positions[pos_key]
            else:
                pos.avg_entry = (pos.avg_entry * pos.quantity + fill.price * fill.quantity) / total_qty
                pos.quantity = total_qty
        else:
            self.positions[pos_key] = Position(
                symbol=fill.symbol,
                side=fill.side,
                quantity=fill.quantity * side_mult,
                avg_entry=fill.price,
                timestamp=fill.timestamp,
            )

    def stop(self) -> None:
        self._running = False
