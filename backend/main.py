"""FastAPI main application."""

import logging

from fastapi import FastAPI

from backend.api.middleware.cors import setup_cors
from backend.api.routes import (
    analyze_router,
    api_keys_router,
    attributions_router,
    health_router,
    publish_router,
    query_router,
    scrape_router,
    tokens_router,
)
from backend.redis_cache import close_redis_cache, init_redis_cache
from backend.middleware.caching import CacheMiddleware, configure_hot_endpoints, get_cache_manager
from backend.middleware.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
)

setup_cors(app)

# Add rate limiting middleware (Redis-backed, extends RHO #55)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
)

# Add caching middleware for hot endpoints
app.add_middleware(
    CacheMiddleware,
    default_ttl=300,  # 5 minutes default
)

# Register all routers
app.include_router(health_router)
app.include_router(scrape_router)
app.include_router(analyze_router)
app.include_router(query_router)
app.include_router(api_keys_router)
app.include_router(tokens_router)
app.include_router(publish_router)
app.include_router(attributions_router)


@app.get("/")
async def root():
    return {"message": "IAC-032 Unified Scraper API", "docs": "/docs"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting IAC-032 Unified Scraper API...")

    # Initialize Redis cache
    try:
        cache = await init_redis_cache()
        logger.info("Redis cache initialized successfully")

        # Configure hot endpoint caching
        cache_manager = get_cache_manager()
        configure_hot_endpoints(cache_manager)
        logger.info("Hot endpoint caching configured")

    except Exception as e:
        logger.error(f"Failed to initialize Redis cache: {e}")
        logger.warning("API will run without caching and rate limiting")

    # TODO: Initialize database connection pool
    # TODO: Verify all services are healthy
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down IAC-032 Unified Scraper API...")

    # Close Redis connection
    try:
        await close_redis_cache()
        logger.info("Redis cache closed")
    except Exception as e:
        logger.error(f"Error closing Redis cache: {e}")

    # TODO: Close database connections
    logger.info("API shutdown complete")
