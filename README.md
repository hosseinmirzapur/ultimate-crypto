# Pulse

Multi-asset, multi-venue crypto market data and research system.

**Exchanges:** KuCoin (perpetuals), Toobit (USDT-M perps), Wallex (Iranian margin + OTC)  
**News:** Arzdigital, TGJU, Bertina Radar, Bitycle  
**Interface:** Dark dashboard + FastAPI backend  
**Deployment:** Docker Compose

## Quick start

```bash
cp .env.example .env
# Fill in exchange API keys in .env

docker compose up --build
```

Open http://localhost

## Views

- **Home** — live price cards, connection status, active signals
- **Markets** — sortable table, click any row for candle chart
- **Signals** — strategy-generated opportunities with confidence
- **Backtest** — run basis/funding arb strategies against historical data
- **News** — aggregated Iranian + global crypto headlines
- **Settings** — exchange status, data retention, refresh rate

## Config

| File | Purpose |
|------|---------|
| `config/exchanges.yaml` | Exchange credentials, symbols, endpoints |
| `config/retention.yaml` | Data retention policies (days) |
| `config/dashboard.yaml` | UI preferences |
| `.env` | Secrets and overrides |

## Adding an exchange

1. Create `src/pulse/exchanges/{name}/adapter.py` implementing `ExchangeClient`
2. Add entry to `config/exchanges.yaml`
3. Register normalizer in `src/pulse/models/normalize.py`
4. Done — no core changes needed

## Stack

- Backend: FastAPI + uvicorn
- Frontend: Vanilla JS, no build step
- Charts: Canvas (self-hosted, no CDN)
- Storage: InfluxDB (time-series) + SQLModel (relational)
- Runtime: Docker Compose
- Package: `uv`

## Architecture

```
exchanges/  → adapters (no vendor logic in core)
models/     → canonical schema + normalizer registry
transport/  → WS manager + rate limiter
storage/    → InfluxDB + SQLModel
features/   → indicators + cross-venue analytics
strategies/ → signal generation
backtest/   → event-driven engine with realistic fills
api/        → FastAPI routes + WebSocket
dashboard/  → static HTML/CSS/JS, self-hosted
```

## Development

```bash
uv sync
uv run pytest
uv run uvicorn pulse.api.app:create_app --factory --reload
```
