"""TGJU news provider."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from pulse.news.base import NewsProvider

logger = logging.getLogger(__name__)


class TGJUProvider(NewsProvider):
    name = "tgju"
    url = "https://www.tgju.org"

    async def fetch(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.url)
            resp.raise_for_status()
        # TODO: parse
        return []
