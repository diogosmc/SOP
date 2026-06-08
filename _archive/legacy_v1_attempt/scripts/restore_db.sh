#!/usr/bin/env bash
# Restore PostgreSQL database for COPILOTO
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup_file.sql>"
  exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

source "${ROOT_DIR}/.env" 2>/dev/null || true

POSTGRES_USER="${POSTGRES_USER:-copiloto}"
POSTGRES_DB="${POSTGRES_DB:-copiloto}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "Restoring ${POSTGRES_DB} from ${BACKUP_FILE}..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -f "$BACKUP_FILE"

echo "Restore complete."
