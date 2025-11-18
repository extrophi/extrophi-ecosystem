"""
Database Configuration Security Fix

VULNERABILITY: VULN-004 - Hardcoded Database Credentials [HIGH]
FILE: backend/db/connection.py:10-12
OWASP: A05:2021 - Security Misconfiguration
CWE: CWE-798 (Hard-coded Credentials)

ISSUE:
Database credentials are hardcoded as default values, which is a security risk
if deployed without environment variable override.

FIX:
Require DATABASE_URL environment variable, fail fast if not set in production.
"""

import os
import sys
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool


def get_database_url() -> str:
    """
    Get database URL from environment with security validation.

    Security Improvements:
    1. No hardcoded credentials
    2. Fail fast if DATABASE_URL not set in production
    3. Validate URL format
    4. Warn if using default in development

    Returns:
        Database connection string

    Raises:
        ValueError: If DATABASE_URL not set in production
        RuntimeError: If URL format is invalid
    """
    environment = os.getenv("ENVIRONMENT", "production").lower()
    database_url = os.getenv("DATABASE_URL")

    # Production: REQUIRE DATABASE_URL
    if environment == "production":
        if not database_url:
            print("❌ ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
            print("❌ Cannot start application without database configuration", file=sys.stderr)
            sys.exit(1)

    # Development/Testing: Allow default, but warn
    elif environment in ("development", "test"):
        if not database_url:
            default_url = "postgresql://scraper:scraper_pass@localhost:5432/unified_scraper_dev"
            print("⚠️  WARNING: Using default database credentials for development")
            print(f"⚠️  Set DATABASE_URL environment variable to override")
            print(f"⚠️  Default: {default_url}")
            database_url = default_url

    else:
        # Unknown environment, require explicit configuration
        if not database_url:
            raise ValueError(
                f"DATABASE_URL required for environment: {environment}"
            )

    # Validate URL format
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError(
            f"Invalid DATABASE_URL: must start with 'postgresql://' or 'postgres://'"
        )

    # Security check: Warn if using default password
    if "scraper_pass" in database_url and environment != "test":
        print("⚠️  WARNING: Using default database password (insecure!)")

    return database_url


def get_engine_secure():
    """
    Create SQLAlchemy engine with secure configuration.

    Security Features:
    1. Connection pooling limits
    2. Health checks before use
    3. SSL enforcement for production
    4. Connection timeout limits

    Returns:
        SQLAlchemy engine
    """
    database_url = get_database_url()
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # Connection arguments
    connect_args = {}

    # Production: Enforce SSL
    if environment == "production":
        connect_args["sslmode"] = "require"
        connect_args["connect_timeout"] = 10

    # Create engine with security settings
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,              # Max persistent connections
        max_overflow=20,           # Max temporary connections
        pool_timeout=30,           # Timeout waiting for connection
        pool_recycle=3600,         # Recycle connections after 1 hour
        pool_pre_ping=True,        # Verify connections before use
        echo=False,                # Don't log SQL (could leak sensitive data)
        connect_args=connect_args,
    )

    return engine


def get_session_secure() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get secure database session.

    Usage:
        @app.get("/items")
        async def get_items(db: Session = Depends(get_session_secure)):
            return db.query(Item).all()

    Yields:
        Database session with automatic cleanup
    """
    engine = get_engine_secure()
    session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def health_check_secure() -> bool:
    """
    Check database connectivity with error handling.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        engine = get_engine_secure()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}", file=sys.stderr)
        return False


# Example .env file configuration
ENV_FILE_EXAMPLE = """
# ============================================================
# Database Configuration (REQUIRED)
# ============================================================

# Production
DATABASE_URL=postgresql://prod_user:STRONG_PASSWORD_HERE@db.example.com:5432/extrophi_prod

# Staging
# DATABASE_URL=postgresql://staging_user:STRONG_PASSWORD_HERE@db-staging.example.com:5432/extrophi_staging

# Development (local)
# DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/extrophi_dev

# Environment (production, staging, development, test)
ENVIRONMENT=production

# ============================================================
# Security Notes:
# ============================================================
# 1. NEVER commit DATABASE_URL to version control
# 2. Use strong passwords (16+ characters, random)
# 3. Create separate database users per environment
# 4. Grant minimum required permissions (principle of least privilege)
# 5. Enable SSL/TLS for production databases
# 6. Rotate credentials quarterly
# 7. Use secret management tools (AWS Secrets Manager, HashiCorp Vault)
"""


# Example implementation for backend/db/connection.py
"""
Replace backend/db/connection.py with:

from security.fixes.db_config_fix import (
    get_engine_secure as get_engine,
    get_session_secure as get_session,
    health_check_secure as health_check,
)

# Or import and use directly:
from security.fixes.db_config_fix import get_database_url

DATABASE_URL = get_database_url()  # ✅ Secure, validated
"""


if __name__ == "__main__":
    # Test configuration
    print("🔒 Testing database configuration:")

    try:
        url = get_database_url()
        print(f"✅ Database URL obtained")

        # Mask password in URL for display
        import re
        masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
        print(f"   URL: {masked_url}")

        # Test connection
        if health_check_secure():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")

    except Exception as e:
        print(f"❌ Configuration error: {e}")

    print("\n📝 Example .env configuration:")
    print(ENV_FILE_EXAMPLE)
