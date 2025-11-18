#!/usr/bin/env python3
"""
Database Migration Runner
Applies SQL migration scripts to the PostgreSQL database
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_connection(database_url: str = None):
    """
    Create database connection from environment or provided URL

    Args:
        database_url: PostgreSQL connection string (optional)

    Returns:
        psycopg2 connection object
    """
    if not database_url:
        database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/unified_scraper')

    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def create_migrations_table(conn):
    """
    Create migrations tracking table if it doesn't exist

    Args:
        conn: psycopg2 connection object
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(64)
            )
        """)
        conn.commit()
        print("✓ Migrations table ready")


def get_applied_migrations(conn):
    """
    Get list of already applied migrations

    Args:
        conn: psycopg2 connection object

    Returns:
        Set of migration names
    """
    with conn.cursor() as cur:
        cur.execute("SELECT migration_name FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn, migration_file: Path, dry_run: bool = False):
    """
    Apply a single migration file

    Args:
        conn: psycopg2 connection object
        migration_file: Path to migration SQL file
        dry_run: If True, don't actually apply the migration
    """
    migration_name = migration_file.stem

    # Skip rollback files
    if 'rollback' in migration_name:
        return

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql = f.read()

    if dry_run:
        print(f"[DRY RUN] Would apply: {migration_name}")
        return

    try:
        with conn.cursor() as cur:
            # Execute migration
            cur.execute(sql)

            # Record migration
            cur.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                (migration_name,)
            )

        conn.commit()
        print(f"✓ Applied: {migration_name}")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Failed to apply {migration_name}: {e}")
        sys.exit(1)


def rollback_migration(conn, migration_name: str, migrations_dir: Path, dry_run: bool = False):
    """
    Rollback a single migration

    Args:
        conn: psycopg2 connection object
        migration_name: Name of migration to rollback
        migrations_dir: Path to migrations directory
        dry_run: If True, don't actually rollback
    """
    rollback_file = migrations_dir / f"{migration_name}_rollback.sql"

    if not rollback_file.exists():
        print(f"✗ Rollback file not found: {rollback_file}")
        sys.exit(1)

    # Read rollback SQL
    with open(rollback_file, 'r') as f:
        sql = f.read()

    if dry_run:
        print(f"[DRY RUN] Would rollback: {migration_name}")
        return

    try:
        with conn.cursor() as cur:
            # Execute rollback
            cur.execute(sql)

            # Remove from migrations table
            cur.execute(
                "DELETE FROM schema_migrations WHERE migration_name = %s",
                (migration_name,)
            )

        conn.commit()
        print(f"✓ Rolled back: {migration_name}")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Failed to rollback {migration_name}: {e}")
        sys.exit(1)


def list_migrations(conn, migrations_dir: Path):
    """
    List all migrations and their status

    Args:
        conn: psycopg2 connection object
        migrations_dir: Path to migrations directory
    """
    applied = get_applied_migrations(conn)

    # Get all migration files (excluding rollbacks)
    migration_files = sorted([
        f for f in migrations_dir.glob('*.sql')
        if 'rollback' not in f.stem
    ])

    print("\nMigrations Status:")
    print("-" * 60)

    for migration_file in migration_files:
        name = migration_file.stem
        status = "✓ Applied" if name in applied else "○ Pending"
        print(f"{status:12} {name}")

    print("-" * 60)
    print(f"Applied: {len(applied)}, Pending: {len(migration_files) - len(applied)}\n")


def main():
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('command', choices=['up', 'down', 'list', 'status'],
                       help='Migration command: up (apply), down (rollback), list, status')
    parser.add_argument('--migration', '-m', help='Specific migration to apply/rollback')
    parser.add_argument('--database-url', '-d', help='Database connection URL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would happen without applying')
    parser.add_argument('--migrations-dir', default='migrations',
                       help='Path to migrations directory (default: migrations)')

    args = parser.parse_args()

    # Setup paths
    migrations_dir = Path(__file__).parent / args.migrations_dir
    if not migrations_dir.exists():
        print(f"✗ Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Connect to database
    conn = get_db_connection(args.database_url)

    # Create migrations tracking table
    create_migrations_table(conn)

    # Execute command
    if args.command in ['list', 'status']:
        list_migrations(conn, migrations_dir)

    elif args.command == 'up':
        applied = get_applied_migrations(conn)

        if args.migration:
            # Apply specific migration
            migration_file = migrations_dir / f"{args.migration}.sql"
            if not migration_file.exists():
                print(f"✗ Migration not found: {migration_file}")
                sys.exit(1)

            if args.migration in applied:
                print(f"○ Already applied: {args.migration}")
            else:
                apply_migration(conn, migration_file, args.dry_run)
        else:
            # Apply all pending migrations
            migration_files = sorted([
                f for f in migrations_dir.glob('*.sql')
                if 'rollback' not in f.stem and f.stem not in applied
            ])

            if not migration_files:
                print("○ No pending migrations")
            else:
                print(f"Applying {len(migration_files)} migration(s)...\n")
                for migration_file in migration_files:
                    apply_migration(conn, migration_file, args.dry_run)

    elif args.command == 'down':
        if not args.migration:
            print("✗ Must specify migration to rollback with --migration")
            sys.exit(1)

        applied = get_applied_migrations(conn)
        if args.migration not in applied:
            print(f"○ Migration not applied: {args.migration}")
        else:
            rollback_migration(conn, args.migration, migrations_dir, args.dry_run)

    # Close connection
    conn.close()
    print("\n✓ Migration runner complete")


if __name__ == '__main__':
    main()
