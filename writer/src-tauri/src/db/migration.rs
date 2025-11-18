//! Database migration module for schema upgrades

use rusqlite::{Connection, Result as SqliteResult};

/// Get the current schema version from the database
pub fn get_schema_version(conn: &Connection) -> SqliteResult<i32> {
    conn.query_row(
        "SELECT value FROM metadata WHERE key = 'schema_version'",
        [],
        |row| {
            let version_str: String = row.get(0)?;
            Ok(version_str.parse().unwrap_or(0))
        },
    )
}

/// Run all necessary migrations to bring database up to date
pub fn run_migrations(conn: &Connection) -> SqliteResult<()> {
    let current_version = get_schema_version(conn).unwrap_or(0);

    // Migration from v7 to v8: Add privacy_level, published, and git_sha to chat_sessions
    if current_version < 8 {
        migrate_v7_to_v8(conn)?;
    }

    Ok(())
}

/// Migration from schema v7 to v8
/// Adds privacy_level, published, and git_sha columns to chat_sessions table
fn migrate_v7_to_v8(conn: &Connection) -> SqliteResult<()> {
    println!("Migrating database from v7 to v8...");

    // Check if columns already exist (defensive programming)
    let has_privacy_level = check_column_exists(conn, "chat_sessions", "privacy_level")?;
    let has_published = check_column_exists(conn, "chat_sessions", "published")?;
    let has_git_sha = check_column_exists(conn, "chat_sessions", "git_sha")?;

    // Add privacy_level column if it doesn't exist
    if !has_privacy_level {
        conn.execute(
            "ALTER TABLE chat_sessions ADD COLUMN privacy_level TEXT CHECK(privacy_level IN ('PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'))",
            [],
        )?;
        println!("  ✓ Added privacy_level column");
    }

    // Add published column if it doesn't exist
    if !has_published {
        conn.execute(
            "ALTER TABLE chat_sessions ADD COLUMN published INTEGER DEFAULT 0",
            [],
        )?;
        println!("  ✓ Added published column");
    }

    // Add git_sha column if it doesn't exist
    if !has_git_sha {
        conn.execute("ALTER TABLE chat_sessions ADD COLUMN git_sha TEXT", [])?;
        println!("  ✓ Added git_sha column");
    }

    // Create indexes for the new columns (if they don't exist)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_privacy ON chat_sessions(privacy_level)",
        [],
    )?;
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_published ON chat_sessions(published)",
        [],
    )?;
    println!("  ✓ Created indexes for new columns");

    // Update schema version
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES ('schema_version', '8', CURRENT_TIMESTAMP)",
        [],
    )?;
    println!("  ✓ Updated schema version to 8");

    println!("Migration to v8 completed successfully!");

    Ok(())
}

/// Helper function to check if a column exists in a table
fn check_column_exists(
    conn: &Connection,
    table_name: &str,
    column_name: &str,
) -> SqliteResult<bool> {
    let mut stmt = conn.prepare(&format!("PRAGMA table_info({})", table_name))?;

    let columns: Vec<String> = stmt
        .query_map([], |row| row.get(1))?
        .collect::<SqliteResult<Vec<_>>>()?;

    Ok(columns.contains(&column_name.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::initialize_db;

    #[test]
    fn test_get_schema_version() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let version = get_schema_version(&conn).unwrap();
        assert_eq!(version, 8);
    }

    #[test]
    fn test_migration_v7_to_v8() {
        let conn = Connection::open(":memory:").unwrap();

        // Create a v7 database schema (without new columns)
        conn.execute("PRAGMA foreign_keys = ON", []).unwrap();
        conn.execute_batch(
            "
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            INSERT INTO metadata (key, value) VALUES ('schema_version', '7');
            ",
        )
        .unwrap();

        // Verify we're at v7
        assert_eq!(get_schema_version(&conn).unwrap(), 7);

        // Run migration
        migrate_v7_to_v8(&conn).unwrap();

        // Verify schema version updated to v8
        assert_eq!(get_schema_version(&conn).unwrap(), 8);

        // Verify new columns exist
        assert!(check_column_exists(&conn, "chat_sessions", "privacy_level").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "published").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "git_sha").unwrap());

        // Verify old columns still exist
        assert!(check_column_exists(&conn, "chat_sessions", "id").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "title").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "created_at").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "updated_at").unwrap());
    }

    #[test]
    fn test_migration_preserves_data() {
        let conn = Connection::open(":memory:").unwrap();

        // Create v7 schema and insert test data
        conn.execute("PRAGMA foreign_keys = ON", []).unwrap();
        conn.execute_batch(
            "
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            INSERT INTO metadata (key, value) VALUES ('schema_version', '7');
            INSERT INTO chat_sessions (title) VALUES ('Test Session 1');
            INSERT INTO chat_sessions (title) VALUES ('Test Session 2');
            ",
        )
        .unwrap();

        // Verify data exists before migration
        let count_before: i64 = conn
            .query_row("SELECT COUNT(*) FROM chat_sessions", [], |row| row.get(0))
            .unwrap();
        assert_eq!(count_before, 2);

        // Run migration
        migrate_v7_to_v8(&conn).unwrap();

        // Verify data still exists after migration
        let count_after: i64 = conn
            .query_row("SELECT COUNT(*) FROM chat_sessions", [], |row| row.get(0))
            .unwrap();
        assert_eq!(count_after, 2);

        // Verify we can query the data with new columns
        let mut stmt = conn
            .prepare("SELECT id, title, privacy_level, published, git_sha FROM chat_sessions")
            .unwrap();
        let sessions: Vec<(i64, String, Option<String>, i64, Option<String>)> = stmt
            .query_map([], |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)))
            .unwrap()
            .collect::<SqliteResult<Vec<_>>>()
            .unwrap();

        assert_eq!(sessions.len(), 2);
        assert_eq!(sessions[0].1, "Test Session 1");
        assert_eq!(sessions[0].2, None); // privacy_level should be NULL
        assert_eq!(sessions[0].3, 0); // published should be 0 (default)
        assert_eq!(sessions[0].4, None); // git_sha should be NULL
    }

    #[test]
    fn test_check_column_exists() {
        let conn = Connection::open(":memory:").unwrap();

        conn.execute_batch(
            "
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            ",
        )
        .unwrap();

        assert!(check_column_exists(&conn, "test_table", "id").unwrap());
        assert!(check_column_exists(&conn, "test_table", "name").unwrap());
        assert!(!check_column_exists(&conn, "test_table", "nonexistent").unwrap());
    }

    #[test]
    fn test_idempotent_migration() {
        let conn = Connection::open(":memory:").unwrap();

        // Create v7 schema
        conn.execute("PRAGMA foreign_keys = ON", []).unwrap();
        conn.execute_batch(
            "
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            INSERT INTO metadata (key, value) VALUES ('schema_version', '7');
            ",
        )
        .unwrap();

        // Run migration twice
        migrate_v7_to_v8(&conn).unwrap();
        migrate_v7_to_v8(&conn).unwrap();

        // Should still be at v8
        assert_eq!(get_schema_version(&conn).unwrap(), 8);

        // Columns should exist
        assert!(check_column_exists(&conn, "chat_sessions", "privacy_level").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "published").unwrap());
        assert!(check_column_exists(&conn, "chat_sessions", "git_sha").unwrap());
    }
}
