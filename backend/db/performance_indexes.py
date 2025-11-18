"""Performance optimization indexes for database queries.

This module adds indexes to improve query performance for common access patterns.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def add_performance_indexes(session: Session) -> dict[str, str]:
    """
    Add performance indexes to database tables.

    Returns:
        Dictionary with status of each index creation
    """
    results = {}

    # Index definitions for common query patterns
    indexes = [
        # Contents table - frequently filtered/sorted columns
        (
            "idx_contents_scraped_at_desc",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contents_scraped_at_desc "
            "ON contents (scraped_at DESC)"
        ),
        (
            "idx_contents_analyzed_at_not_null",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contents_analyzed_at_not_null "
            "ON contents (analyzed_at) WHERE analyzed_at IS NOT NULL"
        ),
        (
            "idx_contents_embedding_not_null",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contents_embedding_not_null "
            "ON contents (id) WHERE embedding IS NOT NULL"
        ),
        (
            "idx_contents_platform_scraped",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contents_platform_scraped "
            "ON contents (platform, scraped_at DESC)"
        ),

        # Authors table - search optimization
        (
            "idx_authors_username_trigram",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_authors_username_trigram "
            "ON authors USING gin (username gin_trgm_ops)"
        ),
        (
            "idx_authors_display_name_trigram",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_authors_display_name_trigram "
            "ON authors USING gin (display_name gin_trgm_ops)"
        ),

        # Patterns table - performance for pattern queries
        (
            "idx_patterns_confidence_score_desc",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patterns_confidence_score_desc "
            "ON patterns (confidence_score DESC NULLS LAST)"
        ),
        (
            "idx_patterns_discovered_at_desc",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patterns_discovered_at_desc "
            "ON patterns (discovered_at DESC)"
        ),

        # Research sessions - active sessions lookup
        (
            "idx_research_sessions_status_created",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_sessions_status_created "
            "ON research_sessions (status, created_at DESC)"
        ),

        # Users table - login performance
        (
            "idx_users_email_lower",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower "
            "ON users (LOWER(email))"
        ),
        (
            "idx_users_username_lower",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_lower "
            "ON users (LOWER(username))"
        ),

        # Cards table - common queries
        (
            "idx_cards_user_created_desc",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cards_user_created_desc "
            "ON cards (user_id, created_at DESC)"
        ),
        (
            "idx_cards_published_desc",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cards_published_desc "
            "ON cards (is_published, published_at DESC) WHERE is_published = true"
        ),

        # Extropy ledger - transaction queries
        (
            "idx_extropy_ledger_user_type_created",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extropy_ledger_user_type_created "
            "ON extropy_ledger (to_user_id, transaction_type, created_at DESC)"
        ),

        # API keys - rate limiting lookups
        (
            "idx_api_keys_hash_active",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_hash_active "
            "ON api_keys (key_hash, is_active) WHERE is_active = true AND is_revoked = false"
        ),
    ]

    # Enable required extensions first
    try:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        results["pg_trgm_extension"] = "enabled"
    except Exception as e:
        results["pg_trgm_extension"] = f"error: {str(e)}"

    # Create indexes
    for index_name, sql in indexes:
        try:
            session.execute(text(sql))
            session.commit()
            results[index_name] = "created"
        except Exception as e:
            session.rollback()
            results[index_name] = f"error: {str(e)}"

    return results


def analyze_tables(session: Session) -> dict[str, str]:
    """
    Run ANALYZE on all tables to update query planner statistics.

    Returns:
        Dictionary with status of each ANALYZE operation
    """
    results = {}

    tables = [
        "contents",
        "authors",
        "patterns",
        "research_sessions",
        "users",
        "cards",
        "extropy_ledger",
        "attributions",
        "api_keys"
    ]

    for table in tables:
        try:
            session.execute(text(f"ANALYZE {table}"))
            session.commit()
            results[table] = "analyzed"
        except Exception as e:
            session.rollback()
            results[table] = f"error: {str(e)}"

    return results


def get_slow_queries(session: Session, min_calls: int = 10) -> list[dict]:
    """
    Get statistics on slow queries from pg_stat_statements.

    Args:
        min_calls: Minimum number of calls to include query

    Returns:
        List of slow queries with statistics
    """
    try:
        # Enable pg_stat_statements if not already
        session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
        session.commit()

        query = text("""
            SELECT
                calls,
                mean_exec_time::numeric(10,2) as avg_time_ms,
                total_exec_time::numeric(10,2) as total_time_ms,
                LEFT(query, 100) as query_preview,
                shared_blks_hit,
                shared_blks_read
            FROM pg_stat_statements
            WHERE calls >= :min_calls
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """)

        result = session.execute(query, {"min_calls": min_calls})

        return [
            {
                "calls": row[0],
                "avg_time_ms": float(row[1]),
                "total_time_ms": float(row[2]),
                "query": row[3],
                "cache_hit_ratio": (
                    float(row[4]) / (float(row[4]) + float(row[5]))
                    if (row[4] + row[5]) > 0
                    else 0
                ),
            }
            for row in result
        ]
    except Exception as e:
        return [{"error": str(e)}]
