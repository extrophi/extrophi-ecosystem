"""FastAPI main application."""

import logging

from fastapi import FastAPI

from backend.api.middleware.caching import setup_cache_middleware
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
)

# Setup middleware
setup_cors(app)

# Setup API response caching
setup_cache_middleware(
    app,
    default_ttl=300,  # 5 minutes default
    max_cache_size=1000,  # Store up to 1000 responses
    exclude_paths=["/health", "/docs", "/openapi.json", "/redoc"],
    cache_query_params=True
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

    # Initialize database connection pool
    from backend.db.connection import get_engine
    engine = get_engine()

    try:
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection pool initialized")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")

    # Log cache configuration
    from backend.api.middleware.caching import get_cache_stats
    logger.info("✓ API response caching enabled")

    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API...")

    # Close database connections
    from backend.db.connection import get_engine
    engine = get_engine()
    engine.dispose()
    logger.info("✓ Database connections closed")

    logger.info("API shutdown complete")
