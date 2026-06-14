#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COUNT="${1:-10}"

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
else
  echo "Docker Compose is required to run the zero-install sample generator." >&2
  exit 1
fi

cd "$ROOT_DIR"
"${COMPOSE[@]}" run --rm --build --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace \
  backend \
  python scripts/generate_sample_labels.py --count "$COUNT" --clean

echo "Upload files from: $ROOT_DIR/sample_data/generated_labels"
