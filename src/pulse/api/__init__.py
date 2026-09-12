"""API routes."""

from pulse.api.routes import (
    markets_router,
    signals_router,
    backtest_router,
    news_router,
    settings_router,
)
from pulse.api.websocket import router as ws_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(markets_router, prefix="/markets", tags=["markets"])
router.include_router(signals_router, prefix="/signals", tags=["signals"])
router.include_router(backtest_router, prefix="/backtest", tags=["backtest"])
router.include_router(news_router, prefix="/news", tags=["news"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(ws_router, prefix="/ws", tags=["websocket"])