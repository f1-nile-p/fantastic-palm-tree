#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Please review and update passwords."
fi

echo "Starting PO Processing Pipeline..."
docker compose up -d --build

echo "Waiting for services to be healthy..."
sleep 10

echo ""
echo "✅ PO Pipeline is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Qdrant UI: http://localhost:6333/dashboard"
