#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"
echo "Stopping PO Processing Pipeline..."
docker compose down
echo "✅ Pipeline stopped."
