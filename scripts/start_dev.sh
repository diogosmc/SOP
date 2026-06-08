#!/usr/bin/env bash
# Start COPILOTO development stack (Docker infra)
# Uso: ./scripts/start_dev.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
  echo "    Edit .env before production use (passwords, JWT_SECRET_KEY)."
fi

echo "==> Starting Docker Compose (PostgreSQL + Redis)"
docker compose up -d

echo ""
echo "Waiting for healthy containers..."
sleep 3
docker compose ps

echo ""
echo "==> Next steps (run in separate terminals):"
echo ""
echo "  # 1. Migrations"
echo "  cd backend && pip install -r requirements.txt && python -m alembic upgrade head"
echo ""
echo "  # 2. Backend"
echo "  cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  # 3. Frontend"
echo "  cd frontend && npm install && npm run dev"
echo ""
echo "  # 4. Ollama (if not running)"
echo "  ollama serve"
echo "  ollama pull llama3.2:3b && ollama pull mistral:7b-instruct && ollama pull nomic-embed-text"
echo ""
echo "  Open: http://localhost:5173"
echo "  Health: ./scripts/check_health.sh"
