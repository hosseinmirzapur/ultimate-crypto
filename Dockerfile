# Multi-stage Dockerfile for Pulse

FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml README.md .
RUN uv sync --no-dev

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY src/ ./src/
COPY config/ ./config/
EXPOSE 8000
CMD ["uvicorn", "pulse.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
