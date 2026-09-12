"""Settings + config REST endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class SettingsResponse(BaseModel):
    env: str
    log_level: str
    data_retention_days: int
    dashboard_refresh_ms: int
    exchanges: list[dict[str, Any]]


@router.get("/", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    from pulse.core.config import load_config
    s = load_config()
    return SettingsResponse(
        env=s.env,
        log_level=s.log_level,
        data_retention_days=s.data_retention_days,
        dashboard_refresh_ms=s.dashboard_refresh_ms,
        exchanges=[{"name": ex.name, "enabled": ex.enabled} for ex in s.exchanges],
    )


@router.post("/retention")
async def set_retention(days: int) -> dict[str, Any]:
    return {"status": "ok", "data_retention_days": days}
