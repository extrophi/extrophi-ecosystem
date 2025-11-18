"""FastAPI main application."""

from fastapi import FastAPI

from backend.api.middleware.cors import setup_cors
from backend.api.routes import (
    analyze_router,
    api_keys_router,
    attributions_router,
    audit_router,
    health_router,
    publish_router,
    query_router,
    scrape_router,
    tokens_router,
)
from backend.middleware.audit import setup_audit_logging

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
)

setup_cors(app)
setup_audit_logging(app)

# Register all routers
app.include_router(health_router)
app.include_router(scrape_router)
app.include_router(analyze_router)
app.include_router(query_router)
app.include_router(api_keys_router)
app.include_router(tokens_router)
app.include_router(publish_router)
app.include_router(attributions_router)
app.include_router(audit_router)


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
