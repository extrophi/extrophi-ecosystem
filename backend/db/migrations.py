"""Database migration utilities"""

import os
from pathlib import Path

from sqlalchemy import text

from backend.db.connection import get_engine


def run_sql_file(sql_file_path: str) -> bool:
    """
    Execute SQL file against the database.

    Args:
        sql_file_path: Path to SQL file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read SQL file
        sql_path = Path(sql_file_path)
        if not sql_path.exists():
            print(f"SQL file not found: {sql_file_path}")
            return False

        with open(sql_path, "r") as f:
            sql_content = f.read()

        # Execute SQL
        engine = get_engine()
        with engine.connect() as connection:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            for statement in statements:
                if statement:
                    connection.execute(text(statement))
            connection.commit()

        print(f"Successfully executed SQL file: {sql_file_path}")
        return True

    except Exception as e:
        print(f"Error executing SQL file: {e}")
        return False


def apply_schema() -> bool:
    """
    Apply the main schema.sql file.

    Returns:
        True if successful, False otherwise
    """
    # Get schema.sql path relative to this file
    current_dir = Path(__file__).parent
    schema_path = current_dir / "schema.sql"

    return run_sql_file(str(schema_path))


def verify_pgvector() -> bool:
    """
    Verify pgvector extension is installed and enabled.

    Returns:
        True if pgvector is available, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            has_vector = result.scalar() is not None

            if not has_vector:
                print("pgvector extension not found!")
                print("Please install pgvector: https://github.com/pgvector/pgvector")
                return False

            print("pgvector extension verified")
            return True

    except Exception as e:
        print(f"Error checking pgvector: {e}")
        return False


def create_test_data() -> bool:
    """
    Create sample test data for development.

    Returns:
        True if successful, False otherwise
    """
    try:
        from backend.db.repository import AuthorRepository, ContentRepository
        from backend.db.connection import get_session

        # Get a database session
        session_gen = get_session()
        session = next(session_gen)

        try:
            author_repo = AuthorRepository(session)
            content_repo = ContentRepository(session)

            # Create test author
            author = author_repo.create(
                author_id="test_twitter_user",
                platform="twitter",
                username="testuser",
                display_name="Test User",
                bio="This is a test author for development",
                follower_count="10000",
                following_count="500",
                content_count="1000",
                authority_score="0.85",
                profile_url="https://twitter.com/testuser",
            )

            # Create test content
            test_embedding = [0.1] * 1536  # Dummy embedding for testing

            content = content_repo.create(
                platform="twitter",
                source_url="https://twitter.com/testuser/status/123456789",
                author_id=author.id,
                content_title=None,
                content_body="This is a test tweet for development and testing purposes.",
                metrics={
                    "likes": 100,
                    "retweets": 25,
                    "replies": 10,
                    "views": 5000,
                },
                embedding=test_embedding,
            )

            print(f"Created test author: {author.username}")
            print(f"Created test content: {content.id}")
            return True

        finally:
            session.close()

    except Exception as e:
        print(f"Error creating test data: {e}")
        return False


def reset_database(confirm: bool = False) -> bool:
    """
    DANGEROUS: Drop all tables and recreate schema.

    Args:
        confirm: Must be True to execute

    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        print("ERROR: reset_database requires confirm=True")
        return False

    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Drop all tables
            connection.execute(text("DROP TABLE IF EXISTS scrape_jobs CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS content_analysis CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS research_sessions CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS patterns CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS contents CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS authors CASCADE"))
            connection.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column CASCADE"))
            connection.commit()

        print("Dropped all tables")

        # Reapply schema
        if apply_schema():
            print("Database reset complete")
            return True
        else:
            print("Error reapplying schema")
            return False

    except Exception as e:
        print(f"Error resetting database: {e}")
        return False


if __name__ == "__main__":
    """CLI for running migrations"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migrations.py [apply|verify|test-data|reset]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "apply":
        print("Applying schema...")
        success = apply_schema()
        sys.exit(0 if success else 1)

    elif command == "verify":
        print("Verifying pgvector...")
        success = verify_pgvector()
        sys.exit(0 if success else 1)

    elif command == "test-data":
        print("Creating test data...")
        success = create_test_data()
        sys.exit(0 if success else 1)

    elif command == "reset":
        print("WARNING: This will DELETE ALL DATA!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm == "YES":
            success = reset_database(confirm=True)
            sys.exit(0 if success else 1)
        else:
            print("Aborted")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
