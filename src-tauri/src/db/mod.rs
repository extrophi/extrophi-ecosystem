//! Database module for SQLite persistence

use rusqlite::{Connection, Result as SqliteResult};
use std::path::PathBuf;

pub mod models;
pub mod repository;

pub use models::*;
pub use repository::Repository;

/// Initialize database with schema
pub fn initialize_db(db_path: PathBuf) -> SqliteResult<Connection> {
    let conn = Connection::open(db_path)?;

    // Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON", [])?;

    // Load schema
    let schema = include_str!("schema.sql");
    conn.execute_batch(schema)?;

    Ok(conn)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initialize_db() {
        let conn = initialize_db(":memory:".into()).unwrap();

        // Verify tables exist
        let tables: Vec<String> = conn
            .prepare("SELECT name FROM sqlite_master WHERE type='table'")
            .unwrap()
            .query_map([], |row| row.get(0))
            .unwrap()
            .collect::<SqliteResult<Vec<_>>>()
            .unwrap();

        assert!(tables.contains(&"recordings".to_string()));
        assert!(tables.contains(&"transcripts".to_string()));
        assert!(tables.contains(&"segments".to_string()));
        assert!(tables.contains(&"metadata".to_string()));
    }

    #[test]
    fn test_foreign_keys_enabled() {
        let conn = initialize_db(":memory:".into()).unwrap();

        // Check foreign keys are enabled
        let fk_enabled: i32 = conn
            .query_row("PRAGMA foreign_keys", [], |row| row.get(0))
            .unwrap();

        assert_eq!(fk_enabled, 1);
    }

    #[test]
    fn test_schema_version() {
        let conn = initialize_db(":memory:".into()).unwrap();

        // Check schema version
        let version: String = conn
            .query_row(
                "SELECT value FROM metadata WHERE key = 'schema_version'",
                [],
                |row| row.get(0),
            )
            .unwrap();

        assert_eq!(version, "7");  // Updated schema version after migrations
    }

    #[test]
    fn test_indexes_created() {
        let conn = initialize_db(":memory:".into()).unwrap();

        // Verify indexes exist
        let indexes: Vec<String> = conn
            .prepare("SELECT name FROM sqlite_master WHERE type='index'")
            .unwrap()
            .query_map([], |row| row.get(0))
            .unwrap()
            .collect::<SqliteResult<Vec<_>>>()
            .unwrap();

        // Check key indexes
        assert!(indexes.iter().any(|i| i.contains("idx_recordings_created")));
        assert!(indexes
            .iter()
            .any(|i| i.contains("idx_transcripts_recording")));
        assert!(indexes.iter().any(|i| i.contains("idx_transcripts_plugin")));
        assert!(indexes
            .iter()
            .any(|i| i.contains("idx_segments_transcript")));
    }
}
