"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pulse.api import router as api_router
from pulse.core.events import EventBus

logger = logging.getLogger(__name__)
event_bus = EventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pulse starting up")
    yield
    logger.info("Pulse shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pulse",
        description="Multi-venue crypto market data and research",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    app.state.event_bus = event_bus

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
