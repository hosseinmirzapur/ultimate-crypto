"""Cross-venue analytics — basis, arbitrage, relative volume."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def basis_spread(price_a: float, price_b: float) -> float:
    """Return basis spread as percentage: (price_a - price_b) / price_b * 100."""
    if price_b == 0:
        return 0.0
    return (price_a - price_b) / price_b * 100.0


def relative_volume(volume_24h: float, avg_volume_7d: float) -> float:
    """Volume ratio vs 7-day average."""
    if avg_volume_7d == 0:
        return 0.0
    return volume_24h / avg_volume_7d
