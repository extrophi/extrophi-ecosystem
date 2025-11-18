#!/usr/bin/env python3
"""
Migration runner for Backend module database schema
Usage:
    python migrate.py apply   # Apply all migrations
    python migrate.py rollback 001  # Rollback specific migration
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_connection():
    """Get PostgreSQL connection from environment variables"""
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "unified_scraper"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }

    conn = psycopg2.connect(**db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def apply_migration(conn, migration_file: Path):
    """Apply a migration SQL file"""
    print(f"Applying migration: {migration_file.name}")

    with open(migration_file, 'r') as f:
        sql = f.read()

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        print(f"✅ Migration {migration_file.name} applied successfully")
    except Exception as e:
        print(f"❌ Error applying migration {migration_file.name}: {e}")
        raise
    finally:
        cursor.close()


def rollback_migration(conn, migration_name: str):
    """Rollback a migration using its rollback SQL file"""
    migrations_dir = Path(__file__).parent
    rollback_file = migrations_dir / f"{migration_name}_rollback.sql"

    if not rollback_file.exists():
        print(f"❌ Rollback file not found: {rollback_file}")
        sys.exit(1)

    print(f"Rolling back migration: {migration_name}")

    with open(rollback_file, 'r') as f:
        sql = f.read()

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        print(f"✅ Migration {migration_name} rolled back successfully")
    except Exception as e:
        print(f"❌ Error rolling back migration {migration_name}: {e}")
        raise
    finally:
        cursor.close()


def apply_all_migrations(conn):
    """Apply all migration files in order"""
    migrations_dir = Path(__file__).parent

    # Find all migration files (exclude rollback files and this script)
    migration_files = sorted([
        f for f in migrations_dir.glob("*.sql")
        if not f.name.endswith("_rollback.sql")
    ])

    if not migration_files:
        print("No migrations found")
        return

    for migration_file in migration_files:
        apply_migration(conn, migration_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [apply|rollback] [migration_name]")
        sys.exit(1)

    command = sys.argv[1]

    conn = get_db_connection()

    try:
        if command == "apply":
            apply_all_migrations(conn)
        elif command == "rollback":
            if len(sys.argv) < 3:
                print("Usage: python migrate.py rollback <migration_name>")
                sys.exit(1)
            migration_name = sys.argv[2]
            rollback_migration(conn, migration_name)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python migrate.py [apply|rollback] [migration_name]")
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
