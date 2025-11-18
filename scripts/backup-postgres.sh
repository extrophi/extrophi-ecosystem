#!/usr/bin/env bash
#
# PostgreSQL Daily Backup Script
# Part of PROD-DELTA backup and disaster recovery system
#
# This script creates compressed PostgreSQL database backups with:
# - Timestamped filenames
# - 7-day rotation policy
# - Error handling and logging
#
# Usage:
#   ./backup-postgres.sh
#
# Environment variables:
#   BACKUP_DIR       - Directory to store backups (default: /var/backups/extrophi/postgres)
#   DB_HOST          - PostgreSQL host (default: localhost)
#   DB_PORT          - PostgreSQL port (default: 5432)
#   DB_NAME          - Database name (default: research_db)
#   DB_USER          - PostgreSQL user (default: postgres)
#   PGPASSWORD       - PostgreSQL password (set this in environment)
#   RETENTION_DAYS   - Number of days to keep backups (default: 7)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/var/backups/extrophi/postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-research_db}"
DB_USER="${DB_USER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Logging function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "${LOG_FILE}"
}

log "========================================="
log "PostgreSQL Backup Started"
log "========================================="
log "Database: ${DB_NAME}"
log "Host: ${DB_HOST}:${DB_PORT}"
log "User: ${DB_USER}"
log "Backup file: ${BACKUP_FILE}"

# Check if PostgreSQL client tools are available
if ! command -v pg_dump &> /dev/null; then
    log "ERROR: pg_dump not found. Please install PostgreSQL client tools."
    exit 1
fi

# Test database connection
if ! PGPASSWORD="${PGPASSWORD:-}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c '\q' 2>/dev/null; then
    log "ERROR: Cannot connect to PostgreSQL database ${DB_NAME} at ${DB_HOST}:${DB_PORT}"
    log "Please check DB_HOST, DB_PORT, DB_USER, and PGPASSWORD environment variables."
    exit 1
fi

log "Database connection successful"

# Create backup
log "Creating backup..."
if PGPASSWORD="${PGPASSWORD:-}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    2>> "${LOG_FILE}" | gzip > "${BACKUP_FILE}"; then

    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "Backup created successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    log "ERROR: Backup failed"
    exit 1
fi

# Verify backup integrity
log "Verifying backup integrity..."
if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log "Backup integrity verified"
else
    log "ERROR: Backup file is corrupted"
    exit 1
fi

# Rotate old backups (keep last RETENTION_DAYS days)
log "Rotating old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "postgres_${DB_NAME}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "postgres_${DB_NAME}_*.sql.gz" -type f | wc -l)
log "Rotation complete. ${REMAINING_BACKUPS} backup(s) remaining."

# Summary
log "========================================="
log "PostgreSQL Backup Completed Successfully"
log "========================================="
log "Backup file: ${BACKUP_FILE}"
log "Backup size: ${BACKUP_SIZE}"
log "Backups retained: ${REMAINING_BACKUPS}"
log ""

exit 0
