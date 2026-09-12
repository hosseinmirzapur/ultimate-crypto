"""News provider base class."""

from __future__ import annotations

from abc import ABC, abstractmethod


class NewsProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        """Return list of normalized news items."""
