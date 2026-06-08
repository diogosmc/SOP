#!/usr/bin/env bash
# Backup PostgreSQL database for COPILOTO
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${ROOT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/copiloto_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

source "${ROOT_DIR}/.env" 2>/dev/null || true

POSTGRES_USER="${POSTGRES_USER:-copiloto}"
POSTGRES_DB="${POSTGRES_DB:-copiloto}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "Backing up ${POSTGRES_DB} to ${BACKUP_FILE}..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -F p \
  -f "$BACKUP_FILE"

echo "Backup complete: ${BACKUP_FILE}"
