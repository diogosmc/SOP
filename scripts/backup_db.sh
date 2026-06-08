#!/usr/bin/env bash
# Backup PostgreSQL — COPILOTO V1
# Uso: ./scripts/backup_db.sh
# Requer: Docker (copiloto_postgres) ou pg_dump local + .env configurado
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${ROOT_DIR}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/copiloto_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

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

echo "==> COPILOTO backup"
echo "    Database: ${POSTGRES_DB}"
echo "    Output:   ${BACKUP_FILE}"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo "    Method:   docker exec ${CONTAINER}"
  docker exec "$CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -F p \
    > "$BACKUP_FILE"
elif command -v pg_dump >/dev/null 2>&1; then
  echo "    Method:   pg_dump (host)"
  PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -F p \
    -f "$BACKUP_FILE"
else
  echo "ERROR: Neither Docker container '${CONTAINER}' nor pg_dump found."
  echo "Start Docker: docker compose up -d"
  exit 1
fi

echo "Backup complete: ${BACKUP_FILE}"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
