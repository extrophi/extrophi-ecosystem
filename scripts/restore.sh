#!/usr/bin/env bash
#
# Database Restore Script
# Part of PROD-DELTA backup and disaster recovery system
#
# This script restores databases from backups created by backup-postgres.sh and backup-sqlite.sh
#
# Usage:
#   ./restore.sh postgres [backup-file]    # Restore PostgreSQL
#   ./restore.sh sqlite [backup-file]      # Restore SQLite
#   ./restore.sh list postgres             # List PostgreSQL backups
#   ./restore.sh list sqlite               # List SQLite backups
#
# If backup-file is not specified, the script will show available backups and prompt for selection.
#
# Environment variables (PostgreSQL):
#   BACKUP_DIR       - Directory containing backups (default: /var/backups/extrophi/postgres)
#   DB_HOST          - PostgreSQL host (default: localhost)
#   DB_PORT          - PostgreSQL port (default: 5432)
#   DB_NAME          - Database name (default: research_db)
#   DB_USER          - PostgreSQL user (default: postgres)
#   PGPASSWORD       - PostgreSQL password
#
# Environment variables (SQLite):
#   BACKUP_DIR       - Directory containing backups (default: /var/backups/extrophi/sqlite)
#   SQLITE_DB_PATH   - Path to SQLite database (default: ~/.braindump/data/braindump.db)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +"%Y-%m-%d %H:%M:%S")]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +"%Y-%m-%d %H:%M:%S")] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +"%Y-%m-%d %H:%M:%S")] ERROR:${NC} $1"
}

# Usage information
usage() {
    cat << EOF
Database Restore Script

Usage:
  $0 postgres [backup-file]    Restore PostgreSQL database
  $0 sqlite [backup-file]      Restore SQLite database
  $0 list postgres             List available PostgreSQL backups
  $0 list sqlite               List available SQLite backups

Examples:
  $0 list postgres
  $0 postgres /var/backups/extrophi/postgres/postgres_research_db_20250118_120000.sql.gz
  $0 sqlite
  $0 sqlite /var/backups/extrophi/sqlite/sqlite_braindump_20250118_120000.db.gz

Environment Variables:
  PostgreSQL:
    BACKUP_DIR, DB_HOST, DB_PORT, DB_NAME, DB_USER, PGPASSWORD

  SQLite:
    BACKUP_DIR, SQLITE_DB_PATH

EOF
    exit 1
}

# List available backups
list_backups() {
    local db_type="$1"

    if [ "$db_type" = "postgres" ]; then
        local backup_dir="${BACKUP_DIR:-/var/backups/extrophi/postgres}"
        local db_name="${DB_NAME:-research_db}"
        log "PostgreSQL backups in ${backup_dir}:"
        echo ""
        find "${backup_dir}" -name "postgres_${db_name}_*.sql.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
            sort -rn | \
            awk '{print $2}' | \
            while read -r file; do
                size=$(du -h "$file" | cut -f1)
                date=$(stat -c %y "$file" | cut -d. -f1)
                echo "  $(basename "$file") - ${size} - ${date}"
            done
    elif [ "$db_type" = "sqlite" ]; then
        local backup_dir="${BACKUP_DIR:-/var/backups/extrophi/sqlite}"
        log "SQLite backups in ${backup_dir}:"
        echo ""
        find "${backup_dir}" -name "sqlite_*.db.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
            sort -rn | \
            awk '{print $2}' | \
            while read -r file; do
                size=$(du -h "$file" | cut -f1)
                date=$(stat -c %y "$file" | cut -d. -f1)
                echo "  $(basename "$file") - ${size} - ${date}"
            done
    fi
    echo ""
}

# Restore PostgreSQL database
restore_postgres() {
    local backup_file="$1"

    # Configuration
    local backup_dir="${BACKUP_DIR:-/var/backups/extrophi/postgres}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_name="${DB_NAME:-research_db}"
    local db_user="${DB_USER:-postgres}"

    log "========================================="
    log "PostgreSQL Restore"
    log "========================================="
    log "Database: ${db_name}"
    log "Host: ${db_host}:${db_port}"
    log "Backup file: ${backup_file}"
    echo ""

    # Check if backup file exists
    if [ ! -f "${backup_file}" ]; then
        error "Backup file not found: ${backup_file}"
        exit 1
    fi

    # Verify backup integrity
    log "Verifying backup integrity..."
    if ! gzip -t "${backup_file}" 2>/dev/null; then
        error "Backup file is corrupted"
        exit 1
    fi
    log "Backup integrity verified"

    # Check PostgreSQL connection
    if ! command -v psql &> /dev/null; then
        error "psql not found. Please install PostgreSQL client tools."
        exit 1
    fi

    if ! PGPASSWORD="${PGPASSWORD:-}" psql -h "${db_host}" -p "${db_port}" -U "${db_user}" -d "${db_name}" -c '\q' 2>/dev/null; then
        error "Cannot connect to PostgreSQL database ${db_name} at ${db_host}:${db_port}"
        exit 1
    fi

    # Confirm restore (this is destructive!)
    warn "This will REPLACE the current database with the backup!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi

    # Create a pre-restore backup
    log "Creating pre-restore backup as safety measure..."
    local prerestore_backup="${backup_dir}/postgres_${db_name}_prerestore_$(date +%Y%m%d_%H%M%S).sql.gz"
    PGPASSWORD="${PGPASSWORD:-}" pg_dump -h "${db_host}" -p "${db_port}" -U "${db_user}" -d "${db_name}" \
        --format=plain --no-owner --no-acl | gzip > "${prerestore_backup}"
    log "Pre-restore backup saved: ${prerestore_backup}"

    # Drop and recreate database
    log "Dropping and recreating database..."
    PGPASSWORD="${PGPASSWORD:-}" psql -h "${db_host}" -p "${db_port}" -U "${db_user}" -d postgres << EOF
DROP DATABASE IF EXISTS ${db_name};
CREATE DATABASE ${db_name};
EOF

    # Restore from backup
    log "Restoring database from backup..."
    if gunzip -c "${backup_file}" | PGPASSWORD="${PGPASSWORD:-}" psql -h "${db_host}" -p "${db_port}" -U "${db_user}" -d "${db_name}" > /dev/null 2>&1; then
        log "Database restored successfully!"
    else
        error "Restore failed. Your database may be in an inconsistent state."
        error "Pre-restore backup is available at: ${prerestore_backup}"
        exit 1
    fi

    log "========================================="
    log "PostgreSQL Restore Completed"
    log "========================================="
}

# Restore SQLite database
restore_sqlite() {
    local backup_file="$1"

    # Configuration
    local backup_dir="${BACKUP_DIR:-/var/backups/extrophi/sqlite}"
    local sqlite_db_path="${SQLITE_DB_PATH:-$HOME/.braindump/data/braindump.db}"

    log "========================================="
    log "SQLite Restore"
    log "========================================="
    log "Database: ${sqlite_db_path}"
    log "Backup file: ${backup_file}"
    echo ""

    # Check if backup file exists
    if [ ! -f "${backup_file}" ]; then
        error "Backup file not found: ${backup_file}"
        exit 1
    fi

    # Verify backup integrity
    log "Verifying backup integrity..."
    if ! gzip -t "${backup_file}" 2>/dev/null; then
        error "Backup file is corrupted"
        exit 1
    fi
    log "Backup integrity verified"

    # Check SQLite
    if ! command -v sqlite3 &> /dev/null; then
        error "sqlite3 not found. Please install SQLite."
        exit 1
    fi

    # Confirm restore (this is destructive!)
    if [ -f "${sqlite_db_path}" ]; then
        warn "This will REPLACE the current database with the backup!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log "Restore cancelled"
            exit 0
        fi

        # Create a pre-restore backup
        log "Creating pre-restore backup as safety measure..."
        local prerestore_backup="${sqlite_db_path}.prerestore.$(date +%Y%m%d_%H%M%S)"
        cp "${sqlite_db_path}" "${prerestore_backup}"
        log "Pre-restore backup saved: ${prerestore_backup}"
    fi

    # Decompress and restore
    log "Restoring database from backup..."
    mkdir -p "$(dirname "${sqlite_db_path}")"
    if gunzip -c "${backup_file}" > "${sqlite_db_path}"; then
        log "Database file restored"
    else
        error "Restore failed"
        exit 1
    fi

    # Verify restored database
    log "Verifying restored database..."
    if sqlite3 "${sqlite_db_path}" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "Database integrity verified"
    else
        error "Restored database failed integrity check"
        exit 1
    fi

    log "========================================="
    log "SQLite Restore Completed"
    log "========================================="
}

# Main script
if [ $# -lt 1 ]; then
    usage
fi

COMMAND="$1"

case "$COMMAND" in
    list)
        if [ $# -lt 2 ]; then
            error "Please specify database type: postgres or sqlite"
            usage
        fi
        list_backups "$2"
        ;;
    postgres)
        if [ $# -lt 2 ]; then
            list_backups postgres
            echo ""
            error "Please specify a backup file to restore"
            echo "Usage: $0 postgres <backup-file>"
            exit 1
        fi
        restore_postgres "$2"
        ;;
    sqlite)
        if [ $# -lt 2 ]; then
            list_backups sqlite
            echo ""
            error "Please specify a backup file to restore"
            echo "Usage: $0 sqlite <backup-file>"
            exit 1
        fi
        restore_sqlite "$2"
        ;;
    *)
        error "Unknown command: $COMMAND"
        usage
        ;;
esac

exit 0
