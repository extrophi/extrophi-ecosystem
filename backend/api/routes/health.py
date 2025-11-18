import os
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.middleware.caching import get_cache_stats
from backend.db.connection import get_session

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    chroma_host = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port = os.getenv("CHROMA_PORT", "8000")
    return {
        "status": "healthy",
        "services": {
            "database": os.getenv("DATABASE_URL", "not configured"),
            "redis": os.getenv("REDIS_URL", "not configured"),
            "chromadb": f"{chroma_host}:{chroma_port}",
        },
    }


@router.get("/health/performance")
async def performance_stats(db: Session = Depends(get_session)):
    """
    Detailed performance metrics endpoint.

    Returns cache stats, database pool info, and query performance.
    """
    start_time = time.time()

    # Get cache statistics
    cache_stats = get_cache_stats()

    # Get database pool statistics
    from backend.db.connection import get_engine
    engine = get_engine()
    pool = engine.pool

    pool_stats = {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
        "total_connections": pool.size() + pool.overflow(),
    }

    # Test database query performance
    db_start = time.time()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        db_status = "healthy"
    except Exception as e:
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        db_status = f"error: {str(e)}"

    # Calculate total response time
    response_time_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "ok",
        "response_time_ms": response_time_ms,
        "cache": cache_stats,
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms,
            "pool": pool_stats,
        },
    }


@router.post("/health/cache/clear")
async def clear_cache():
    """Clear all cached API responses."""
    from backend.api.middleware.caching import _cache_middleware

    if _cache_middleware:
        stats_before = _cache_middleware.get_stats()
        count = _cache_middleware.invalidate()
        return {
            "status": "success",
            "cleared": count,
            "stats_before": stats_before,
        }

    return {"status": "error", "message": "Cache middleware not initialized"}


@router.post("/health/cache/cleanup")
async def cleanup_cache():
    """Remove expired cache entries."""
    from backend.api.middleware.caching import _cache_middleware

    if _cache_middleware:
        cleaned = _cache_middleware._cleanup_expired()
        stats = _cache_middleware.get_stats()
        return {
            "status": "success",
            "cleaned": cleaned,
            "stats": stats,
        }

    return {"status": "error", "message": "Cache middleware not initialized"}
