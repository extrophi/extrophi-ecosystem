#!/usr/bin/env python3
"""
Database initialization script

Sets up PostgreSQL database with pgvector extension and schema.
Run this script to initialize the database before starting the API.

Usage:
    python -m db.init_db

Environment variables:
    DATABASE_URL or DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def create_database_if_not_exists(db_manager: DatabaseManager) -> bool:
    """
    Create database if it doesn't exist

    Returns:
        True if database was created, False if it already exists
    """
    # Connect to default postgres database to create our database
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    database = os.getenv("DB_NAME", "research_db")

    # Connection string for postgres database
    admin_conn_str = f"postgresql://{user}:{password}@{host}:{port}/postgres"

    try:
        logger.info(f"Checking if database '{database}' exists...")

        # Connect to postgres database
        conn = await asyncpg.connect(admin_conn_str)

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database
        )

        if exists:
            logger.info(f"Database '{database}' already exists")
            await conn.close()
            return False

        # Create database
        logger.info(f"Creating database '{database}'...")
        await conn.execute(f'CREATE DATABASE "{database}"')
        logger.info(f"Database '{database}' created successfully")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


async def run_schema(db_manager: DatabaseManager) -> None:
    """
    Run schema.sql to set up tables, indexes, and functions
    """
    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    logger.info(f"Reading schema from {schema_path}...")
    schema_sql = schema_path.read_text()

    # Execute schema
    logger.info("Executing schema.sql...")
    async with db_manager.acquire() as conn:
        try:
            # Split by semicolons and execute each statement
            # Note: This is a simple approach. For production, consider using a migration tool.
            await conn.execute(schema_sql)
            logger.info("Schema executed successfully")

        except Exception as e:
            logger.error(f"Error executing schema: {e}")
            raise


async def verify_setup(db_manager: DatabaseManager) -> None:
    """
    Verify database setup is correct
    """
    logger.info("Verifying database setup...")

    async with db_manager.acquire() as conn:
        # Check pgvector extension
        pgvector_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )

        if pgvector_exists:
            logger.info("✓ pgvector extension installed")
        else:
            logger.error("✗ pgvector extension NOT installed")
            raise RuntimeError("pgvector extension not found")

        # Check tables
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )

        table_names = [row['tablename'] for row in tables]
        expected_tables = ['sources', 'contents', 'scrape_jobs']

        for table in expected_tables:
            if table in table_names:
                logger.info(f"✓ Table '{table}' exists")
            else:
                logger.error(f"✗ Table '{table}' NOT found")
                raise RuntimeError(f"Table '{table}' not found")

        # Check functions
        functions = await conn.fetch(
            """
            SELECT proname FROM pg_proc
            WHERE proname IN ('find_similar_content', 'find_similar_content_by_platform', 'get_content_statistics')
            """
        )

        function_names = [row['proname'] for row in functions]
        expected_functions = [
            'find_similar_content',
            'find_similar_content_by_platform',
            'get_content_statistics'
        ]

        for func in expected_functions:
            if func in function_names:
                logger.info(f"✓ Function '{func}' exists")
            else:
                logger.error(f"✗ Function '{func}' NOT found")

        # Check sample data
        source_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
        content_count = await conn.fetchval("SELECT COUNT(*) FROM contents")

        logger.info(f"✓ Sample data: {source_count} sources, {content_count} contents")

    logger.info("Database setup verified successfully!")


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("Research Backend - Database Initialization")
    logger.info("=" * 60)

    db_manager = DatabaseManager()

    try:
        # Step 1: Create database if needed
        logger.info("\n[Step 1/4] Creating database...")
        await create_database_if_not_exists(db_manager)

        # Step 2: Connect to database
        logger.info("\n[Step 2/4] Connecting to database...")
        await db_manager.connect(min_size=2, max_size=5)

        # Step 3: Run schema
        logger.info("\n[Step 3/4] Setting up schema...")
        await run_schema(db_manager)

        # Step 4: Verify setup
        logger.info("\n[Step 4/4] Verifying setup...")
        await verify_setup(db_manager)

        logger.info("\n" + "=" * 60)
        logger.info("✓ Database initialization completed successfully!")
        logger.info("=" * 60)

        # Health check
        health = await db_manager.health_check()
        logger.info(f"\nHealth check: {health}")

    except Exception as e:
        logger.error(f"\n✗ Database initialization failed: {e}")
        raise

    finally:
        # Disconnect
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
