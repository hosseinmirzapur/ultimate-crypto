"""Entrypoint script — initializes DB, then starts uvicorn."""

import asyncio
import logging
import os

from pulse.core.config import load_config
from pulse.storage.influx import InfluxDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    settings = load_config()
    influx = InfluxDBClient(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN", "hermes-token-please-change"),
        org=os.getenv("INFLUXDB_ORG", "hermes"),
        bucket=os.getenv("INFLUXDB_BUCKET", "market-data"),
    )
    # TODO: create retention policy if missing
    logger.info("Initialization complete")


if __name__ == "__main__":
    asyncio.run(init())
