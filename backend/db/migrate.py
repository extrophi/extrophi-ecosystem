#!/usr/bin/env python3
"""
Database migration script for IAC-033 Backend Module

Usage:
    python migrate.py apply    # Apply schema to database
    python migrate.py verify   # Verify schema is applied correctly
    python migrate.py rollback # Drop all tables (DANGEROUS)
    python migrate.py status   # Check current schema version
"""

import os
import sys
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_database_url() -> str:
    """Get PostgreSQL connection URL from environment or use default"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/extrophi_backend"
    )


def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(get_database_url())
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Failed to connect to database: {e}")
        print("\nMake sure PostgreSQL is running and DATABASE_URL is set correctly.")
        print(f"Current DATABASE_URL: {get_database_url()}")
        sys.exit(1)


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    db_url = get_database_url()

    # Parse the URL to extract database name and connection details
    parts = db_url.split('/')
    db_name = parts[-1]
    base_url = '/'.join(parts[:-1]) + '/postgres'  # Connect to default postgres DB

    try:
        conn = psycopg2.connect(base_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )

        if not cursor.fetchone():
            print(f"📦 Creating database '{db_name}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"✅ Database '{db_name}' created successfully")
        else:
            print(f"✅ Database '{db_name}' already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️  Could not create database: {e}")
        print("Proceeding anyway (database might already exist)...")


def read_schema_file() -> str:
    """Read the schema.sql file"""
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)

    return schema_path.read_text()


def apply_schema():
    """Apply the schema to the database"""
    print("🚀 Applying database schema...\n")

    # Create database if needed
    create_database_if_not_exists()

    # Read schema file
    schema_sql = read_schema_file()

    # Connect and apply schema
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Execute schema in a transaction
        cursor.execute(schema_sql)
        conn.commit()

        print("✅ Schema applied successfully!\n")

        # Get schema version
        cursor.execute(
            "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
        )
        version = cursor.fetchone()

        if version:
            print(f"📋 Schema version: {version[0]}")

        # Show table summary
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error applying schema: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


def verify_schema():
    """Verify that all required tables and constraints exist"""
    print("🔍 Verifying database schema...\n")

    conn = get_connection()
    cursor = conn.cursor()

    required_tables = ['users', 'cards', 'attributions', 'extropy_ledger', 'sync_state']
    required_triggers = ['prevent_negative_balance_trigger', 'update_card_extropy_on_attribution']
    required_views = ['user_balance_summary', 'recent_transactions', 'card_attribution_analytics']

    try:
        # Check tables
        print("📋 Checking tables:")
        for table in required_tables:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            """, (table,))

            exists = cursor.fetchone()[0] > 0
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")

        # Check triggers
        print("\n⚡ Checking triggers:")
        for trigger in required_triggers:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.triggers
                WHERE trigger_name = %s
            """, (trigger,))

            exists = cursor.fetchone()[0] > 0
            status = "✅" if exists else "❌"
            print(f"   {status} {trigger}")

        # Check views
        print("\n👁️  Checking views:")
        for view in required_views:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.views
                WHERE table_schema = 'public'
                AND table_name = %s
            """, (view,))

            exists = cursor.fetchone()[0] > 0
            status = "✅" if exists else "❌"
            print(f"   {status} {view}")

        # Check DECIMAL usage (critical requirement)
        print("\n💰 Checking DECIMAL fields (critical):")
        decimal_fields = [
            ('users', 'extropy_balance'),
            ('cards', 'extropy_earned'),
            ('attributions', 'extropy_amount'),
            ('extropy_ledger', 'amount'),
            ('extropy_ledger', 'balance_before'),
            ('extropy_ledger', 'balance_after'),
        ]

        for table, column in decimal_fields:
            cursor.execute("""
                SELECT data_type, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table, column))

            result = cursor.fetchone()
            if result:
                data_type, precision, scale = result
                is_decimal = data_type == 'numeric'
                status = "✅" if is_decimal else "❌"
                print(f"   {status} {table}.{column}: {data_type}({precision},{scale})")
            else:
                print(f"   ❌ {table}.{column}: NOT FOUND")

        # Check schema version
        print("\n📌 Schema version:")
        cursor.execute(
            "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
        )
        version = cursor.fetchone()
        if version:
            print(f"   ✅ Version {version[0]}")
        else:
            print("   ❌ Version not found")

        print("\n✅ Schema verification complete!")

    except Exception as e:
        print(f"\n❌ Error verifying schema: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


def show_status():
    """Show current schema status"""
    print("📊 Database Status\n")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Schema version
        cursor.execute(
            "SELECT key, value FROM schema_metadata ORDER BY key"
        )
        metadata = cursor.fetchall()

        print("Schema Metadata:")
        for key, value in metadata:
            print(f"   • {key}: {value}")

        # Table counts
        print("\nTable Row Counts:")
        tables = ['users', 'cards', 'attributions', 'extropy_ledger', 'sync_state']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   • {table}: {count} rows")

    except Exception as e:
        print(f"❌ Error getting status: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


def rollback_schema():
    """Drop all tables (DANGEROUS - use with caution)"""
    print("⚠️  WARNING: This will DROP ALL TABLES!")
    response = input("Are you sure? Type 'YES' to confirm: ")

    if response != 'YES':
        print("Cancelled.")
        return

    print("\n🗑️  Dropping all tables...\n")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Drop all tables in correct order (respect foreign keys)
        drop_statements = [
            "DROP VIEW IF EXISTS card_attribution_analytics CASCADE",
            "DROP VIEW IF EXISTS recent_transactions CASCADE",
            "DROP VIEW IF EXISTS user_balance_summary CASCADE",
            "DROP TABLE IF EXISTS sync_state CASCADE",
            "DROP TABLE IF EXISTS extropy_ledger CASCADE",
            "DROP TABLE IF EXISTS attributions CASCADE",
            "DROP TABLE IF EXISTS cards CASCADE",
            "DROP TABLE IF EXISTS users CASCADE",
            "DROP TABLE IF EXISTS schema_metadata CASCADE",
        ]

        for statement in drop_statements:
            cursor.execute(statement)
            print(f"   ✅ {statement}")

        conn.commit()
        print("\n✅ All tables dropped successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during rollback: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    commands = {
        'apply': apply_schema,
        'verify': verify_schema,
        'rollback': rollback_schema,
        'status': show_status,
    }

    if command not in commands:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    commands[command]()


if __name__ == '__main__':
    main()
