#!/usr/bin/env bash
# Health check — COPILOTO V1
# Uso: ./scripts/check_health.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

API_HOST="${APP_HOST:-localhost}"
API_PORT="${APP_PORT:-8000}"
BASE="http://${API_HOST}:${API_PORT}"

echo "==> Docker Compose"
if command -v docker >/dev/null 2>&1; then
  docker compose -f "${ROOT_DIR}/docker-compose.yml" ps || true
else
  echo "    docker not found — skip"
fi

echo ""
echo "==> API health"

check_url() {
  local label="$1"
  local url="$2"
  if command -v curl >/dev/null 2>&1; then
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "    OK  ${label} — ${url}"
      curl -s "$url" | head -c 200
      echo ""
    else
      echo "    FAIL ${label} — ${url}"
    fi
  else
    echo "    curl not found — open ${url} manually"
  fi
}

check_url "root" "${BASE}/health"
check_url "detailed" "${BASE}/api/v1/health"
check_url "ai" "${BASE}/api/v1/ai/health"

echo ""
echo "Done."
