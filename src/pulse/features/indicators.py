"""Technical indicators."""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)


def sma(prices: Sequence[float], period: int) -> np.ndarray:
    arr = np.asarray(prices, dtype=float)
    if len(arr) < period:
        return np.full(len(arr), np.nan)
    cumsum = np.cumsum(arr)
    result = np.full(len(arr), np.nan)
    result[period - 1:] = (cumsum[period:] - cumsum[:-period]) / period
    return result


def ema(prices: Sequence[float], period: int) -> np.ndarray:
    arr = np.asarray(prices, dtype=float)
    if len(arr) < period:
        return np.full(len(arr), np.nan)
    k = 2.0 / (period + 1)
    ema_arr = np.zeros(len(arr))
    ema_arr[0] = arr[0]
    for i in range(1, len(arr)):
        ema_arr[i] = arr[i] * k + ema_arr[i - 1] * (1 - k)
    return ema_arr


def rsi(prices: Sequence[float], period: int = 14) -> np.ndarray:
    arr = np.asarray(prices, dtype=float)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.convolve(gains, np.ones(period) / period, mode="full")[: len(arr)]
    avg_loss = np.convolve(losses, np.ones(period) / period, mode="full")[: len(arr)]
    rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
    result = 100.0 - 100.0 / (1.0 + rs)
    return np.concatenate(([np.nan], result))


def macd(
    prices: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line[~np.isnan(macd_line)], signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist
