#!/usr/bin/env bash
# Start the full local stack with Docker Compose.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review the values before going further."
fi

docker compose up --build "$@"
