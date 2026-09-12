"""InfluxDB time-series storage client."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient as _InfluxDBClient, Point

logger = logging.getLogger(__name__)


class InfluxDBClient:
    """Thin wrapper around influxdb_client."""

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
    ) -> None:
        self._client = _InfluxDBClient(url=url, token=token, org=org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        self.org = org

    async def write(self, measurement: str, tags: dict[str, str], fields: dict[str, Any], timestamp: datetime | None = None) -> None:
        point = Point(measurement)
        for k, v in tags.items():
            point.tag(k, v)
        for k, v in fields.items():
            point.field(k, v)
        if timestamp:
            point.time(timestamp)
        self._write_api.write(bucket=self.bucket, record=point)

    async def query(self, flux: str) -> list[dict[str, Any]]:
        query_api = self._client.query_api()
        tables = query_api.query(flux)
        results = []
        for table in tables:
            for record in table.records:
                results.append(record.values)
        return results

    def close(self) -> None:
        self._client.close()
