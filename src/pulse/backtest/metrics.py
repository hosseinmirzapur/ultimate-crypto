"""Performance metrics for backtest results."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def calculate_metrics(result: dict[str, Any]) -> dict[str, Any]:
    fills = result.get("fills", [])
    equity = result.get("equity_curve", [])
    if not fills or not equity:
        return {"error": "insufficient data"}

    returns = []
    for i in range(1, len(equity)):
        prev = equity[i - 1][1]
        curr = equity[i][1]
        if prev != 0:
            returns.append((curr - prev) / prev)

    if not returns:
        return {"error": "no returns"}

    avg = sum(returns) / len(returns)
    variance = sum((r - avg) ** 2 for r in returns) / len(returns)
    std = math.sqrt(variance)

    sharpe = (avg / std * math.sqrt(365)) if std > 0 else 0.0

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns:
        cumulative += r
        peak = max(peak, cumulative)
        dd = peak - cumulative
        max_dd = max(max_dd, dd)

    wins = sum(1 for r in returns if r > 0)
    losses = sum(1 for r in returns if r < 0)
    win_rate = wins / len(returns) if returns else 0.0

    return {
        "total_return_pct": result.get("total_return_pct", 0.0),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "win_rate_pct": round(win_rate * 100, 2),
        "num_trades": len(fills),
        "avg_return_per_trade": round(sum(r for r in returns if r > 0) / max(wins, 1) * 100, 2) if wins else 0.0,
    }
