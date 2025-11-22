#!/usr/bin/env bash
#
# SQLite Daily Backup Script
# Part of PROD-DELTA backup and disaster recovery system
#
# This script creates compressed SQLite database backups with:
# - Timestamped filenames
# - 7-day rotation policy
# - Safe backup using SQLite's .backup command
# - Error handling and logging
#
# Usage:
#   ./backup-sqlite.sh
#
# Environment variables:
#   BACKUP_DIR       - Directory to store backups (default: /var/backups/extrophi/sqlite)
#   SQLITE_DB_PATH   - Path to SQLite database (default: ~/.braindump/data/braindump.db)
#   RETENTION_DAYS   - Number of days to keep backups (default: 7)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/var/backups/extrophi/sqlite}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-$HOME/.braindump/data/braindump.db}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME=$(basename "${SQLITE_DB_PATH}" .db)
BACKUP_FILE="${BACKUP_DIR}/sqlite_${DB_NAME}_${TIMESTAMP}.db"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Logging function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "${LOG_FILE}"
}

log "========================================="
log "SQLite Backup Started"
log "========================================="
log "Database: ${SQLITE_DB_PATH}"
log "Backup file: ${BACKUP_FILE_GZ}"

# Check if SQLite client is available
if ! command -v sqlite3 &> /dev/null; then
    log "ERROR: sqlite3 not found. Please install SQLite."
    exit 1
fi

# Check if database file exists
if [ ! -f "${SQLITE_DB_PATH}" ]; then
    log "WARNING: Database file not found: ${SQLITE_DB_PATH}"
    log "This may be normal if the application hasn't created it yet."
    log "Skipping backup."
    exit 0
fi

log "Database file found ($(du -h "${SQLITE_DB_PATH}" | cut -f1))"

# Create backup using SQLite's .backup command (safe even while DB is in use)
log "Creating backup using SQLite .backup command..."
if sqlite3 "${SQLITE_DB_PATH}" ".backup ${BACKUP_FILE}" 2>> "${LOG_FILE}"; then
    log "Backup created successfully"
else
    log "ERROR: Backup failed"
    exit 1
fi

# Verify backup integrity
log "Verifying backup integrity..."
if sqlite3 "${BACKUP_FILE}" "PRAGMA integrity_check;" | grep -q "ok"; then
    log "Backup integrity verified"
else
    log "ERROR: Backup integrity check failed"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Compress backup
log "Compressing backup..."
if gzip -f "${BACKUP_FILE}"; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE_GZ}" | cut -f1)
    log "Backup compressed: ${BACKUP_FILE_GZ} (${BACKUP_SIZE})"
else
    log "ERROR: Compression failed"
    exit 1
fi

# Verify compressed backup integrity
log "Verifying compressed backup..."
if gzip -t "${BACKUP_FILE_GZ}" 2>/dev/null; then
    log "Compressed backup verified"
else
    log "ERROR: Compressed backup is corrupted"
    exit 1
fi

# Rotate old backups (keep last RETENTION_DAYS days)
log "Rotating old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "sqlite_${DB_NAME}_*.db.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "sqlite_${DB_NAME}_*.db.gz" -type f | wc -l)
log "Rotation complete. ${REMAINING_BACKUPS} backup(s) remaining."

# Summary
log "========================================="
log "SQLite Backup Completed Successfully"
log "========================================="
log "Backup file: ${BACKUP_FILE_GZ}"
log "Backup size: ${BACKUP_SIZE}"
log "Backups retained: ${REMAINING_BACKUPS}"
log ""

exit 0
