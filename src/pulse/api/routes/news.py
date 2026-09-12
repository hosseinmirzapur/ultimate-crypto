"""News REST endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class NewsItemResponse(BaseModel):
    id: int
    source: str
    title: str
    url: str
    published_at: datetime
    sentiment: float | None
    assets: str | None


@router.get("/latest")
async def latest_news(source: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Latest news from all providers."""
    return {"items": []}


@router.get("/sources")
async def list_sources() -> dict[str, Any]:
    return {"sources": ["arzdigital", "tgju", "bertina", "bitycle"]}
