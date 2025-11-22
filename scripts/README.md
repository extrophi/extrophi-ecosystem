# Database Backup & Restore Scripts

**PROD-DELTA**: Automated database backup and disaster recovery system for the Extrophi Ecosystem.

## Overview

This directory contains scripts for backing up and restoring databases:

- **PostgreSQL** (`research_db`) - Used by the research/scraper backend
- **SQLite** (`braindump.db`) - Used by the BrainDump Writer application

All backups are:
- ✅ Compressed with gzip
- ✅ Timestamped (YYYYMMDD_HHMMSS format)
- ✅ Automatically rotated (7-day retention by default)
- ✅ Integrity-verified after creation
- ✅ Logged with detailed output

## Scripts

### 1. `backup-postgres.sh`

Creates compressed PostgreSQL database backups.

**Usage:**
```bash
./scripts/backup-postgres.sh
```

**Environment Variables:**
```bash
BACKUP_DIR=/var/backups/extrophi/postgres  # Backup directory
DB_HOST=localhost                          # PostgreSQL host
DB_PORT=5432                               # PostgreSQL port
DB_NAME=research_db                        # Database name
DB_USER=postgres                           # PostgreSQL user
PGPASSWORD=your_password                   # PostgreSQL password
RETENTION_DAYS=7                           # Days to keep backups
```

**Example:**
```bash
# Run with custom configuration
BACKUP_DIR=/mnt/backups \
DB_HOST=prod-db.example.com \
PGPASSWORD=secret123 \
./scripts/backup-postgres.sh
```

**Output:**
- Backup file: `/var/backups/extrophi/postgres/postgres_research_db_20250118_120000.sql.gz`
- Log file: `/var/backups/extrophi/postgres/backup.log`

---

### 2. `backup-sqlite.sh`

Creates compressed SQLite database backups using SQLite's `.backup` command (safe even while the database is in use).

**Usage:**
```bash
./scripts/backup-sqlite.sh
```

**Environment Variables:**
```bash
BACKUP_DIR=/var/backups/extrophi/sqlite           # Backup directory
SQLITE_DB_PATH=~/.braindump/data/braindump.db    # SQLite database path
RETENTION_DAYS=7                                  # Days to keep backups
```

**Example:**
```bash
# Run with custom configuration
BACKUP_DIR=/mnt/backups \
SQLITE_DB_PATH=/path/to/custom.db \
./scripts/backup-sqlite.sh
```

**Output:**
- Backup file: `/var/backups/extrophi/sqlite/sqlite_braindump_20250118_120000.db.gz`
- Log file: `/var/backups/extrophi/sqlite/backup.log`

---

### 3. `restore.sh`

Restores databases from backup files. Supports both PostgreSQL and SQLite.

**Usage:**
```bash
# List available backups
./scripts/restore.sh list postgres
./scripts/restore.sh list sqlite

# Restore PostgreSQL
./scripts/restore.sh postgres /var/backups/extrophi/postgres/postgres_research_db_20250118_120000.sql.gz

# Restore SQLite
./scripts/restore.sh sqlite /var/backups/extrophi/sqlite/sqlite_braindump_20250118_120000.db.gz
```

**Safety Features:**
- ✅ Verifies backup integrity before restore
- ✅ Creates pre-restore backup as safety measure
- ✅ Requires explicit confirmation (type "yes")
- ✅ Verifies database integrity after restore

**PostgreSQL Environment Variables:**
Same as `backup-postgres.sh`

**SQLite Environment Variables:**
Same as `backup-sqlite.sh`

**Example:**
```bash
# List PostgreSQL backups
./scripts/restore.sh list postgres

# Restore specific PostgreSQL backup
./scripts/restore.sh postgres /var/backups/extrophi/postgres/postgres_research_db_20250118_120000.sql.gz

# Restore SQLite backup
./scripts/restore.sh sqlite /var/backups/extrophi/sqlite/sqlite_braindump_20250118_120000.db.gz
```

---

## Automated Backups (GitHub Actions)

Daily backups run automatically via GitHub Actions at **2:00 AM UTC**.

**Workflow:** `.github/workflows/backup.yml`

**Features:**
- Runs daily on schedule
- Can be manually triggered
- Uploads backups to GitHub Artifacts (90-day retention)
- Generates backup report in GitHub Actions summary
- Sends notifications on failure

**Manual Trigger:**
1. Go to GitHub Actions → "Database Backups" workflow
2. Click "Run workflow"
3. Select backup type: `all`, `postgres`, or `sqlite`
4. Click "Run workflow"

**Required GitHub Secrets:**
```
POSTGRES_HOST       # PostgreSQL host (optional, defaults to localhost)
POSTGRES_PORT       # PostgreSQL port (optional, defaults to 5432)
POSTGRES_DB         # Database name (optional, defaults to research_db)
POSTGRES_USER       # PostgreSQL user (optional, defaults to postgres)
POSTGRES_PASSWORD   # PostgreSQL password (required for production)
SQLITE_DB_PATH      # SQLite database path (optional, defaults to ~/.braindump/data/braindump.db)
```

---

## Setup Instructions

### Local Development

1. **Install dependencies:**
   ```bash
   # macOS
   brew install postgresql sqlite

   # Ubuntu/Debian
   sudo apt-get install postgresql-client sqlite3
   ```

2. **Configure environment variables:**
   ```bash
   # PostgreSQL
   export PGPASSWORD="your_postgres_password"

   # Or create a .env file
   cat > .env << EOF
   BACKUP_DIR=/var/backups/extrophi
   DB_HOST=localhost
   DB_NAME=research_db
   DB_USER=postgres
   PGPASSWORD=your_password
   EOF

   # Load environment
   source .env
   ```

3. **Run backup:**
   ```bash
   ./scripts/backup-postgres.sh
   ./scripts/backup-sqlite.sh
   ```

### Production Deployment

1. **Create backup directories:**
   ```bash
   sudo mkdir -p /var/backups/extrophi/{postgres,sqlite}
   sudo chown -R $USER:$USER /var/backups/extrophi
   ```

2. **Set up cron jobs (alternative to GitHub Actions):**
   ```bash
   # Edit crontab
   crontab -e

   # Add daily backups at 2 AM
   0 2 * * * PGPASSWORD=secret123 /path/to/extrophi-ecosystem/scripts/backup-postgres.sh
   5 2 * * * /path/to/extrophi-ecosystem/scripts/backup-sqlite.sh
   ```

3. **Configure GitHub Secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add required secrets (see "Required GitHub Secrets" above)

4. **Test backups:**
   ```bash
   # Run manual backup
   ./scripts/backup-postgres.sh
   ./scripts/backup-sqlite.sh

   # Verify backup files exist
   ls -lh /var/backups/extrophi/postgres/
   ls -lh /var/backups/extrophi/sqlite/

   # Test restore (use with caution!)
   ./scripts/restore.sh list postgres
   ```

---

## Disaster Recovery

### Quick Recovery Steps

**PostgreSQL:**
```bash
# 1. List available backups
./scripts/restore.sh list postgres

# 2. Restore from backup
./scripts/restore.sh postgres /var/backups/extrophi/postgres/postgres_research_db_YYYYMMDD_HHMMSS.sql.gz

# 3. Verify database
psql -h localhost -U postgres -d research_db -c "SELECT COUNT(*) FROM contents;"
```

**SQLite:**
```bash
# 1. List available backups
./scripts/restore.sh list sqlite

# 2. Restore from backup
./scripts/restore.sh sqlite /var/backups/extrophi/sqlite/sqlite_braindump_YYYYMMDD_HHMMSS.db.gz

# 3. Verify database
sqlite3 ~/.braindump/data/braindump.db "PRAGMA integrity_check;"
```

### Download from GitHub Artifacts

If local backups are lost, download from GitHub:

1. Go to repository → Actions → "Database Backups" workflow
2. Select a successful run
3. Download artifacts:
   - `postgres-backup-NNNN`
   - `sqlite-backup-NNNN`
4. Extract and restore:
   ```bash
   unzip postgres-backup-1234.zip
   ./scripts/restore.sh postgres postgres_research_db_*.sql.gz
   ```

---

## Monitoring

### Check Backup Status

```bash
# View backup logs
tail -f /var/backups/extrophi/postgres/backup.log
tail -f /var/backups/extrophi/sqlite/backup.log

# List recent backups
./scripts/restore.sh list postgres
./scripts/restore.sh list sqlite

# Check backup sizes
du -h /var/backups/extrophi/postgres/
du -h /var/backups/extrophi/sqlite/
```

### GitHub Actions Monitoring

- Check workflow runs: GitHub → Actions → "Database Backups"
- View backup reports in workflow run summary
- Set up notifications for failed workflows

---

## Troubleshooting

### PostgreSQL Connection Issues

**Error:** "Cannot connect to PostgreSQL database"

**Solution:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U postgres -d research_db -c '\q'

# Check PGPASSWORD is set
echo $PGPASSWORD
```

### SQLite Database Not Found

**Warning:** "Database file not found"

**Solution:**
```bash
# Check database path
ls -la ~/.braindump/data/braindump.db

# If database doesn't exist, BrainDump hasn't been run yet
# This is normal and not an error
```

### Backup File Corrupted

**Error:** "Backup file is corrupted"

**Solution:**
```bash
# Verify gzip integrity
gzip -t /var/backups/extrophi/postgres/postgres_research_db_*.sql.gz

# If corrupted, restore from GitHub Artifacts or previous backup
./scripts/restore.sh list postgres
```

### Disk Space Issues

**Error:** "No space left on device"

**Solution:**
```bash
# Check disk space
df -h /var/backups/extrophi

# Manually clean old backups
find /var/backups/extrophi -name "*.sql.gz" -mtime +7 -delete
find /var/backups/extrophi -name "*.db.gz" -mtime +7 -delete
```

---

## Configuration Reference

### Default Backup Locations

| Database | Default Path | Backup Location |
|----------|--------------|-----------------|
| PostgreSQL | `localhost:5432/research_db` | `/var/backups/extrophi/postgres/` |
| SQLite | `~/.braindump/data/braindump.db` | `/var/backups/extrophi/sqlite/` |

### Retention Policy

- **Local backups:** 7 days (configurable via `RETENTION_DAYS`)
- **GitHub Artifacts:** 90 days (GitHub default)
- **Recommended:** Store critical backups in external storage (S3, Google Drive, etc.)

### Backup Schedule

- **GitHub Actions:** Daily at 2:00 AM UTC
- **Cron (optional):** Daily at 2:00 AM local time
- **Manual:** Run scripts anytime

---

## Security Considerations

1. **Passwords:**
   - Never commit passwords to git
   - Use environment variables or GitHub Secrets
   - Store `.env` files outside repository

2. **Backup Storage:**
   - Restrict backup directory permissions: `chmod 700 /var/backups/extrophi`
   - Encrypt backups for external storage
   - Use secure transfer methods (SFTP, S3 with encryption)

3. **Database Access:**
   - Use least-privilege database users for backups
   - Rotate database passwords regularly
   - Audit backup access logs

---

## Related Documentation

- **Issue:** [#97 - PROD-DELTA Backup + Disaster Recovery](https://github.com/extrophi/extrophi-ecosystem/issues/97)
- **Project Docs:** `/docs/pm/MASTER-EXECUTION-PLAN.md`
- **Database Schema:**
  - PostgreSQL: `/backend/db/models.py`, `/research/backend/db/schema.sql`
  - SQLite: `/writer/src-tauri/src/db/schema.sql`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review backup logs
3. Open an issue on GitHub
4. Contact PROD-DELTA team

---

**Last Updated:** 2025-01-18
**Version:** 1.0.0
**Author:** PROD-DELTA (Agent 27)
