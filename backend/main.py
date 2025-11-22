"""FastAPI main application."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api.middleware.cors import setup_cors
from backend.api.middleware.security_headers import setup_security_headers
from backend.api.routes import (
    analyze_router,
    api_keys_router,
    attributions_router,
    health_router,
    publish_router,
    query_router,
    scrape_router,
    tokens_router,
    ultra_learning_router,
)
from backend.security.audit_log import AuditLogger
from backend.security.rate_limiting import get_rate_limiter

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
)

# Initialize security components
audit_logger = AuditLogger()
rate_limiter = get_rate_limiter()

# Setup middleware
setup_cors(app)
setup_security_headers(app)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    client_ip = request.client.host
    endpoint = request.url.path

    # Skip rate limiting for health check
    if endpoint == "/health":
        return await call_next(request)

    # Check rate limit
    if not await rate_limiter.check_rate_limit(client_ip, endpoint):
        audit_logger.log_rate_limit_exceeded(client_ip, endpoint, rate_limiter.max_requests)
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    return await call_next(request)

# Register all routers
app.include_router(health_router)
app.include_router(scrape_router)
app.include_router(analyze_router)
app.include_router(query_router)
app.include_router(api_keys_router)
app.include_router(tokens_router)
app.include_router(publish_router)
app.include_router(attributions_router)
app.include_router(ultra_learning_router)


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
