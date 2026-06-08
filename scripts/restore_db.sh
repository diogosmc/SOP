#!/usr/bin/env bash
# Restore PostgreSQL — COPILOTO V1
# Uso: ./scripts/restore_db.sh backups/copiloto_YYYYMMDD_HHMMSS.sql
# ATENÇÃO: sobrescreve dados atuais do banco copiloto.
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup_file.sql>"
  echo "Example: $0 backups/copiloto_20260607_120000.sql"
  exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-copiloto}"
POSTGRES_DB="${POSTGRES_DB:-copiloto}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
CONTAINER="${POSTGRES_CONTAINER:-copiloto_postgres}"

echo "==> COPILOTO restore"
echo "    Source:   ${BACKUP_FILE}"
echo "    Database: ${POSTGRES_DB}"
echo ""
echo "WARNING: This will REPLACE current data in '${POSTGRES_DB}'."
read -r -p "Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo "    Method:   docker exec ${CONTAINER}"
  docker exec -i "$CONTAINER" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    < "$BACKUP_FILE"
elif command -v psql >/dev/null 2>&1; then
  echo "    Method:   psql (host)"
  PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -f "$BACKUP_FILE"
else
  echo "ERROR: Neither Docker container '${CONTAINER}' nor psql found."
  exit 1
fi

echo "Restore complete."
