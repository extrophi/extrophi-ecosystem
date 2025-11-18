"""FastAPI main application."""

from fastapi import FastAPI

from backend.api.middleware.cors import setup_cors
from backend.api.middleware.versioning import setup_versioning

# Import v1 routes
from backend.api.routes.v1 import (
    analyze_router as v1_analyze_router,
    api_keys_router as v1_api_keys_router,
    attributions_router as v1_attributions_router,
    health_router as v1_health_router,
    publish_router as v1_publish_router,
    query_router as v1_query_router,
    scrape_router as v1_scrape_router,
    tokens_router as v1_tokens_router,
)

# Import v2 routes
from backend.api.routes.v2 import (
    analyze_router as v2_analyze_router,
    api_keys_router as v2_api_keys_router,
    attributions_router as v2_attributions_router,
    health_router as v2_health_router,
    publish_router as v2_publish_router,
    query_router as v2_query_router,
    scrape_router as v2_scrape_router,
    tokens_router as v2_tokens_router,
)

# Import unversioned routes for backwards compatibility
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

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.2.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
)

setup_cors(app)
setup_versioning(app)

# Register v1 routers with /v1 prefix
app.include_router(v1_health_router, prefix="/v1")
app.include_router(v1_scrape_router, prefix="/v1")
app.include_router(v1_analyze_router, prefix="/v1")
app.include_router(v1_query_router, prefix="/v1")
app.include_router(v1_api_keys_router, prefix="/v1")
app.include_router(v1_tokens_router, prefix="/v1")
app.include_router(v1_publish_router, prefix="/v1")
app.include_router(v1_attributions_router, prefix="/v1")

# Register v2 routers with /v2 prefix
app.include_router(v2_health_router, prefix="/v2")
app.include_router(v2_scrape_router, prefix="/v2")
app.include_router(v2_analyze_router, prefix="/v2")
app.include_router(v2_query_router, prefix="/v2")
app.include_router(v2_api_keys_router, prefix="/v2")
app.include_router(v2_tokens_router, prefix="/v2")
app.include_router(v2_publish_router, prefix="/v2")
app.include_router(v2_attributions_router, prefix="/v2")

# Register unversioned routers for backwards compatibility (default to v1 behavior)
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
    # TODO: Initialize database connection pool
    # TODO: Verify all services are healthy
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # TODO: Close database connections
    pass
