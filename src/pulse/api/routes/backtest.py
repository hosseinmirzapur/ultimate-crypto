"""Backtest REST endpoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from pulse.backtest.engine import BacktestEngine
from pulse.backtest.fill_models import PerfectFill, RealisticFill
from pulse.backtest.metrics import calculate_metrics
from pulse.strategies.basis_arb import BasisArbStrategy

logger = logging.getLogger(__name__)
router = APIRouter()


class BacktestRequest(BaseModel):
    symbol: str
    exchange: str
    strategy: str = "basis_arb"
    start_date: str
    end_date: str
    initial_capital: float = 100_000.0
    fill_model: str = "realistic"
    slippage_bps: float = 10.0


class BacktestResponse(BaseModel):
    status: str
    metrics: dict[str, Any] | None = None
    error: str | None = None


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(req: BacktestRequest) -> BacktestResponse:
    try:
        strategy = BasisArbStrategy()
        fill_model = (
            RealisticFill(slippage_bps=req.slippage_bps)
            if req.fill_model == "realistic"
            else PerfectFill()
        )
        engine = BacktestEngine(strategy=strategy, fill_model=fill_model, initial_capital=req.initial_capital)
        # TODO: load events from InfluxDB for date range
        result = await engine.run()
        metrics = calculate_metrics(result)
        return BacktestResponse(status="ok", metrics=metrics)
    except Exception as exc:
        logger.exception("Backtest failed")
        return BacktestResponse(status="error", error=str(exc))
