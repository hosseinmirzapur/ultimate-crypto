"""Dev startup script."""

#!/usr/bin/env bash
set -euo pipefail

echo "Starting Pulse in dev mode..."
docker compose up --build
