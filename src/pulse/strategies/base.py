from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Strategy(ABC):
    name: str = "base"

    @abstractmethod
    async def on_signal(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Return a signal dict or None."""
