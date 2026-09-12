from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ExecutionEngine(ABC):
    mode: str = "base"

    @abstractmethod
    async def submit(self, order: dict[str, Any]) -> dict[str, Any]:
        """Submit an order, return fill result."""

    @abstractmethod
    async def cancel(self, order_id: str) -> None:
        """Cancel an open order."""

    @abstractmethod
    async def positions(self) -> list[dict[str, Any]]:
        """Return current positions."""
