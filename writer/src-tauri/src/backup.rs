//! Database backup and restore functionality

use chrono::{DateTime, Utc};
use rusqlite::Connection;
use std::fs;
use std::path::{Path, PathBuf};

use crate::error::BrainDumpError;

/// Backup manager for SQLite database
pub struct BackupManager {
    db_path: PathBuf,
    backup_dir: PathBuf,
}

/// Information about a backup file
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BackupInfo {
    pub file_path: String,
    pub file_name: String,
    pub file_size_bytes: i64,
    pub created_at: DateTime<Utc>,
    pub is_automatic: bool,
}

impl BackupManager {
    /// Create a new backup manager
    pub fn new(db_path: PathBuf, backup_dir: PathBuf) -> Result<Self, BrainDumpError> {
        // Create backup directory if it doesn't exist
        if !backup_dir.exists() {
            fs::create_dir_all(&backup_dir).map_err(|e| {
                BrainDumpError::Io(format!("Failed to create backup directory: {}", e))
            })?;
        }

        Ok(Self {
            db_path,
            backup_dir,
        })
    }

    /// Get default backup directory for the platform
    pub fn get_default_backup_dir() -> PathBuf {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));

        #[cfg(target_os = "macos")]
        return home.join("Library/Application Support/BrainDump/Backups");

        #[cfg(target_os = "linux")]
        return home.join(".braindump/backups");

        #[cfg(target_os = "windows")]
        return home.join("AppData/Local/BrainDump/Backups");

        #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
        return home.join(".braindump/backups");
    }

    /// Create a backup of the database
    pub fn create_backup(&self, is_automatic: bool) -> Result<BackupInfo, BrainDumpError> {
        crate::logging::info(
            "Backup",
            &format!("Creating backup from: {}", self.db_path.display()),
        );

        // Verify source database exists
        if !self.db_path.exists() {
            return Err(BrainDumpError::Io(format!(
                "Database file not found: {}",
                self.db_path.display()
            )));
        }

        // Generate backup filename with timestamp
        let timestamp = Utc::now();
        let backup_name = format!("braindump_backup_{}.db", timestamp.format("%Y%m%d_%H%M%S"));
        let backup_path = self.backup_dir.join(&backup_name);

        crate::logging::info(
            "Backup",
            &format!("Backup destination: {}", backup_path.display()),
        );

        // Use SQLite VACUUM INTO for clean, compact backup
        let conn = Connection::open(&self.db_path)
            .map_err(|e| BrainDumpError::Io(format!("Failed to open database: {}", e)))?;

        // VACUUM INTO creates a clean copy of the database
        conn.execute(&format!("VACUUM INTO '{}'", backup_path.display()), [])
            .map_err(|e| BrainDumpError::Io(format!("Failed to create backup: {}", e)))?;

        drop(conn);

        // Get file size
        let metadata = fs::metadata(&backup_path).map_err(|e| {
            BrainDumpError::Io(format!("Failed to get backup file metadata: {}", e))
        })?;

        let file_size_bytes = metadata.len() as i64;

        crate::logging::info(
            "Backup",
            &format!(
                "Backup created successfully: {} ({} bytes)",
                backup_name, file_size_bytes
            ),
        );

        Ok(BackupInfo {
            file_path: backup_path.to_string_lossy().to_string(),
            file_name: backup_name,
            file_size_bytes,
            created_at: timestamp,
            is_automatic,
        })
    }

    /// Restore database from a backup file
    pub fn restore_backup(&self, backup_path: &Path) -> Result<(), BrainDumpError> {
        crate::logging::info(
            "Backup",
            &format!("Restoring from backup: {}", backup_path.display()),
        );

        // Verify backup file exists
        if !backup_path.exists() {
            return Err(BrainDumpError::Io(format!(
                "Backup file not found: {}",
                backup_path.display()
            )));
        }

        // Verify backup is a valid SQLite database
        Connection::open(backup_path).map_err(|e| {
            BrainDumpError::Io(format!(
                "Invalid backup file (not a SQLite database): {}",
                e
            ))
        })?;

        // Create safety backup of current DB before restoring
        crate::logging::info("Backup", "Creating safety backup before restore");
        let safety_backup = self.create_backup(false)?;
        crate::logging::info(
            "Backup",
            &format!("Safety backup created: {}", safety_backup.file_path),
        );

        // Close any open connections to the database
        // (In production, this should be handled by the caller)

        // Replace current DB with backup
        fs::copy(backup_path, &self.db_path)
            .map_err(|e| BrainDumpError::Io(format!("Failed to restore backup: {}", e)))?;

        crate::logging::info("Backup", "Database restored successfully");

        Ok(())
    }

    /// List all backup files in the backup directory
    pub fn list_backups(&self) -> Result<Vec<BackupInfo>, BrainDumpError> {
        if !self.backup_dir.exists() {
            return Ok(vec![]);
        }

        let mut backups = Vec::new();

        let entries = fs::read_dir(&self.backup_dir)
            .map_err(|e| BrainDumpError::Io(format!("Failed to read backup directory: {}", e)))?;

        for entry in entries {
            let entry = entry.map_err(|e| {
                BrainDumpError::Io(format!("Failed to read directory entry: {}", e))
            })?;
            let path = entry.path();

            // Only include .db files
            if path.extension().and_then(|s| s.to_str()) != Some("db") {
                continue;
            }

            // Get file metadata
            let metadata = fs::metadata(&path)
                .map_err(|e| BrainDumpError::Io(format!("Failed to get file metadata: {}", e)))?;

            let file_name = path
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();

            // Try to parse timestamp from filename
            let created_at = metadata
                .created()
                .ok()
                .and_then(|t| {
                    DateTime::from_timestamp(
                        t.duration_since(std::time::UNIX_EPOCH).ok()?.as_secs() as i64,
                        0,
                    )
                })
                .unwrap_or_else(|| Utc::now());

            // Determine if automatic based on filename pattern
            let is_automatic = file_name.starts_with("braindump_backup_");

            backups.push(BackupInfo {
                file_path: path.to_string_lossy().to_string(),
                file_name,
                file_size_bytes: metadata.len() as i64,
                created_at,
                is_automatic,
            });
        }

        // Sort by creation time (newest first)
        backups.sort_by(|a, b| b.created_at.cmp(&a.created_at));

        Ok(backups)
    }

    /// Delete a backup file
    pub fn delete_backup(&self, backup_path: &Path) -> Result<(), BrainDumpError> {
        if !backup_path.exists() {
            return Err(BrainDumpError::Io(format!(
                "Backup file not found: {}",
                backup_path.display()
            )));
        }

        fs::remove_file(backup_path)
            .map_err(|e| BrainDumpError::Io(format!("Failed to delete backup: {}", e)))?;

        crate::logging::info(
            "Backup",
            &format!("Backup deleted: {}", backup_path.display()),
        );

        Ok(())
    }

    /// Clean up old backups based on retention count
    pub fn cleanup_old_backups(&self, retention_count: usize) -> Result<usize, BrainDumpError> {
        let backups = self.list_backups()?;

        if backups.len() <= retention_count {
            return Ok(0);
        }

        let to_delete = &backups[retention_count..];
        let mut deleted_count = 0;

        for backup in to_delete {
            let path = Path::new(&backup.file_path);
            if let Err(e) = self.delete_backup(path) {
                crate::logging::error(
                    "Backup",
                    &format!("Failed to delete old backup {}: {}", backup.file_name, e),
                );
            } else {
                deleted_count += 1;
            }
        }

        crate::logging::info(
            "Backup",
            &format!("Cleaned up {} old backup(s)", deleted_count),
        );

        Ok(deleted_count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_backup_manager_creation() {
        let temp_dir = tempdir().unwrap();
        let db_path = temp_dir.path().join("test.db");
        let backup_dir = temp_dir.path().join("backups");

        let manager = BackupManager::new(db_path, backup_dir.clone());
        assert!(manager.is_ok());
        assert!(backup_dir.exists());
    }

    #[test]
    fn test_get_default_backup_dir() {
        let backup_dir = BackupManager::get_default_backup_dir();
        assert!(
            backup_dir.to_string_lossy().contains("BrainDump")
                || backup_dir.to_string_lossy().contains("braindump")
        );
    }
}
