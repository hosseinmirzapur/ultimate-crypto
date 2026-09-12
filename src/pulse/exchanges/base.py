from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ExchangeClient(ABC):
    """Abstract base for all exchange adapters."""

    name: str = "base"

    @abstractmethod
    async def connect(self) -> None:
        """Open WS + any REST sessions."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean shutdown."""

    @abstractmethod
    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to WS channels."""

    @abstractmethod
    def parse_message(self, raw: str | bytes) -> dict[str, Any]:
        """Convert exchange-specific payload to normalized dict."""

    @abstractmethod
    def normalize(self, data: dict[str, Any], data_type: str) -> dict[str, Any]:
        """Map exchange-specific fields to canonical schema."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return connection health status."""
