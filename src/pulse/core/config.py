"""Configuration loader — Pydantic Settings + YAML files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExchangeConfig(BaseSettings):
    name: str
    enabled: bool = True
    api_key: str | None = None
    api_secret: str | None = None
    api_passphrase: str | None = None
    ws_url: str
    rest_url: str
    symbols: list[str] = []
    proxy: str | None = None


class RetentionConfig(BaseSettings):
    market_data_days: int = 90
    news_days: int = 30
    signals_days: int = 30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PULSE_", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    data_retention_days: int = 90
    dashboard_refresh_ms: int = 1000
    exchanges: list[ExchangeConfig] = []
    retention: RetentionConfig = RetentionConfig()


def load_config(config_path: str | None = None) -> Settings:
    base = Path(config_path or Path.cwd() / "config")
    exchanges_raw = _load_yaml(base / "exchanges.yaml")
    retention_raw = _load_yaml(base / "retention.yaml")
    dashboard_raw = _load_yaml(base / "dashboard.yaml")

    exchange_configs: list[ExchangeConfig] = []
    if exchanges_raw:
        for ex in exchanges_raw.get("exchanges", []):
            exchange_configs.append(ExchangeConfig(**ex))

    retention_cfg = RetentionConfig(**(retention_raw.get("retention", {}) if retention_raw else {}))
    dashboard_cfg = dashboard_raw.get("dashboard", {}) if dashboard_raw else {}

    env_overrides: dict[str, Any] = {}
    if os.getenv("PULSE_DATA_RETENTION_DAYS"):
        env_overrides["data_retention_days"] = int(os.getenv("PULSE_DATA_RETENTION_DAYS"))
    if os.getenv("PULSE_DASHBOARD_REFRESH_MS"):
        env_overrides["dashboard_refresh_ms"] = int(os.getenv("PULSE_DASHBOARD_REFRESH_MS"))

    return Settings(
        exchanges=exchange_configs,
        retention=retention_cfg,
        **dashboard_cfg,
        **env_overrides,
    )


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)
