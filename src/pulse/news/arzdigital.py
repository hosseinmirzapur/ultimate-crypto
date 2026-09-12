"""Arzdigital news provider."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from pulse.news.base import NewsProvider

logger = logging.getLogger(__name__)


class ArzdigitalProvider(NewsProvider):
    name = "arzdigital"
    url = "https://arzdigital.com"

    async def fetch(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.url)
            resp.raise_for_status()
        # TODO: parse HTML with selectolax/BeautifulSoup
        return []
