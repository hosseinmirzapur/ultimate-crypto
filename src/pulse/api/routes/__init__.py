"""API routes."""

from pulse.api.routes.markets import router as markets_router
from pulse.api.routes.signals import router as signals_router
from pulse.api.routes.backtest import router as backtest_router
from pulse.api.routes.news import router as news_router
from pulse.api.routes.settings import router as settings_router

__all__ = [
    "markets_router",
    "signals_router",
    "backtest_router",
    "news_router",
    "settings_router",
]
