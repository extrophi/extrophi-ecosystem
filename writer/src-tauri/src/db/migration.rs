//! Database migration utilities

use rusqlite::{Connection, Result as SqliteResult};

/// Get the current schema version from the database
pub fn get_schema_version(conn: &Connection) -> SqliteResult<i32> {
    let version: String = conn
        .query_row(
            "SELECT value FROM metadata WHERE key = 'schema_version'",
            [],
            |row| row.get(0),
        )
        .unwrap_or_else(|_| "0".to_string());

    Ok(version.parse().unwrap_or(0))
}

/// Apply all pending migrations
pub fn apply_migrations(conn: &Connection) -> SqliteResult<()> {
    let current_version = get_schema_version(conn)?;

    // Apply migrations sequentially
    if current_version < 8 {
        migrate_to_v8(conn)?;
    }
    if current_version < 9 {
        migrate_to_v9(conn)?;
    }

    Ok(())
}

/// Migration from V7 to V8: Add cards table with privacy_level, published, git_sha
fn migrate_to_v8(conn: &Connection) -> SqliteResult<()> {
    println!("Migrating database from V7 to V8 (adding cards table)...");

    // Create cards table
    conn.execute_batch(
        "
        -- V8: Cards for Card UI with Privacy & Publishing
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            privacy_level TEXT CHECK(privacy_level IN (
                'PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'
            )),
            published INTEGER DEFAULT 0,
            git_sha TEXT,
            category TEXT CHECK(category IN (
                'UNASSIMILATED', 'PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH', 'JUNK'
            )),
            session_id INTEGER,
            message_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_cards_privacy_level ON cards(privacy_level);
        CREATE INDEX IF NOT EXISTS idx_cards_published ON cards(published);
        CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
        CREATE INDEX IF NOT EXISTS idx_cards_session ON cards(session_id);
        CREATE INDEX IF NOT EXISTS idx_cards_created ON cards(created_at DESC);

        -- Update schema version
        UPDATE metadata SET value = '8' WHERE key = 'schema_version';
        ",
    )?;

    println!("Migration to V8 completed successfully");
    Ok(())
}

/// Migration from V8 to V9: Add card_templates table for template system
fn migrate_to_v9(conn: &Connection) -> SqliteResult<()> {
    println!("Migrating database from V8 to V9 (adding card templates)...");

    // Create card_templates table
    conn.execute_batch(
        "
        -- V9: Card Templates for quick card creation
        CREATE TABLE IF NOT EXISTS card_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT CHECK(category IN (
                'UNASSIMILATED', 'PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH', 'JUNK'
            )),
            is_system INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_templates_name ON card_templates(name);
        CREATE INDEX IF NOT EXISTS idx_templates_system ON card_templates(is_system);

        -- Update schema version
        UPDATE metadata SET value = '9' WHERE key = 'schema_version';
        ",
    )?;

    println!("Migration to V9 completed successfully");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::initialize_db;

    #[test]
    fn test_get_schema_version() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let version = get_schema_version(&conn).unwrap();
        assert_eq!(version, 9);
    }

    #[test]
    fn test_migration_v7_to_v8() {
        let conn = Connection::open(":memory:").unwrap();

        // Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON", []).unwrap();

        // Create V7 schema (without cards table)
        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                recording_id INTEGER,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                privacy_tags TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            );

            INSERT INTO metadata (key, value) VALUES ('schema_version', '7');
            ",
        )
        .unwrap();

        // Verify V7 schema
        let version_before = get_schema_version(&conn).unwrap();
        assert_eq!(version_before, 7);

        // Cards table should not exist
        let cards_exists: i32 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cards'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(cards_exists, 0);

        // Apply migration
        migrate_to_v8(&conn).unwrap();

        // Verify V8 schema
        let version_after = get_schema_version(&conn).unwrap();
        assert_eq!(version_after, 8);

        // Cards table should now exist
        let cards_exists: i32 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cards'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(cards_exists, 1);

        // Verify indexes were created
        let indexes: Vec<String> = conn
            .prepare("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='cards'")
            .unwrap()
            .query_map([], |row| row.get(0))
            .unwrap()
            .collect::<SqliteResult<Vec<_>>>()
            .unwrap();

        assert!(indexes.iter().any(|i| i.contains("idx_cards_privacy_level")));
        assert!(indexes.iter().any(|i| i.contains("idx_cards_published")));
        assert!(indexes.iter().any(|i| i.contains("idx_cards_category")));
    }

    #[test]
    fn test_apply_migrations() {
        let conn = Connection::open(":memory:").unwrap();
        conn.execute("PRAGMA foreign_keys = ON", []).unwrap();

        // Create V7 schema
        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO metadata (key, value) VALUES ('schema_version', '7');

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                recording_id INTEGER,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                privacy_tags TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            );
            ",
        )
        .unwrap();

        // Apply all migrations
        apply_migrations(&conn).unwrap();

        // Verify final version
        let version = get_schema_version(&conn).unwrap();
        assert_eq!(version, 9);
    }
}
