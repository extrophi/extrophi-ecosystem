"""
Main application entry point for Sovereign Backend.

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration. It provides the core application instance that
can be run with Uvicorn or other ASGI servers.

The application includes:
    - CORS middleware for cross-origin requests
    - Request timing middleware for performance monitoring
    - Multi-tenant support middleware
    - Health check and status endpoints
    - API router mounting

Example:
    Run the application in development:
        $ uvicorn src.main:app --reload
        
    Run in production:
        $ uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

Attributes:
    app: The FastAPI application instance
"""

# Standard library imports
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict

# Third-party imports
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# Local application imports
from src.api.v1.api import api_router
from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.diagnostics import DiagnosticError, diagnostic_error_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    This context manager handles startup and shutdown operations for the
    FastAPI application, including database connections, cache initialization,
    and resource cleanup.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Control returns to FastAPI during application runtime
    """
    # Startup operations
    startup_start = time.perf_counter()
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    
    try:
        # Initialize database connections
        await init_db()
        logger.info("✅ Database connections established")
        
        # Log configuration summary
        logger.info(f"📋 Configuration: {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")
        logger.info(f"🌐 CORS origins: {settings.BACKEND_CORS_ORIGINS}")
        logger.info(f"🔧 Features enabled: "
                   f"vector_search={settings.ENABLE_VECTOR_SEARCH}, "
                   f"websockets={settings.ENABLE_WEBSOCKETS}, "
                   f"file_upload={settings.ENABLE_FILE_UPLOAD}, "
                   f"multi_tenant={settings.ENABLE_MULTI_TENANT}")
        
        startup_time = time.perf_counter() - startup_start
        logger.info(f"✨ Application started successfully in {startup_time:.2f}s")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    finally:
        # Shutdown operations
        shutdown_start = time.perf_counter()
        logger.info("👋 Shutting down...")
        
        try:
            # Close database connections
            await close_db()
            logger.info("✅ Database connections closed")
            
            shutdown_time = time.perf_counter() - shutdown_start
            logger.info(f"🛑 Application shut down gracefully in {shutdown_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}", exc_info=True)


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description="A sovereign, production-ready backend with multi-tenancy, "
                "vector search, real-time updates, and enterprise features",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=app_lifespan,
    debug=settings.DEBUG,
)

# Add diagnostic error handler
app.add_exception_handler(DiagnosticError, diagnostic_error_handler)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """
    Add security headers to all responses.
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware or endpoint handler
        
    Returns:
        Response with security headers added
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    **settings.get_cors_settings()
)

# Add trusted host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.sovereign-backend.com", "localhost"]
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable) -> Response:
    """
    Add request processing time to response headers.
    
    This middleware measures the time taken to process each request
    and adds it as an X-Process-Time header for monitoring.
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware or endpoint handler
        
    Returns:
        Response with X-Process-Time header
    """
    start_time = time.perf_counter()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )
    
    return response

# Multi-tenant middleware
@app.middleware("http")
async def extract_tenant_context(request: Request, call_next: Callable) -> Response:
    """
    Extract and validate tenant context from request headers.
    
    This middleware extracts the tenant ID from the configured header
    and attaches it to the request state for use in downstream handlers.
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware or endpoint handler
        
    Returns:
        Response from the next handler
    """
    if settings.ENABLE_MULTI_TENANT:
        # Extract tenant ID from header
        tenant_id = request.headers.get(settings.TENANT_HEADER, "default")
        
        # Validate tenant ID format (alphanumeric and hyphens only)
        if not tenant_id.replace("-", "").isalnum():
            return JSONResponse(
                status_code=400,
                content={
                    "detail": f"Invalid tenant ID format: {tenant_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Attach to request state
        request.state.tenant_id = tenant_id.lower()
        
        # Log tenant context for debugging
        if settings.DEBUG:
            logger.debug(f"Request tenant context: {tenant_id}")
    else:
        # Default tenant for single-tenant mode
        request.state.tenant_id = "default"
    
    response = await call_next(request)
    return response

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle ValueError exceptions globally.
    
    Args:
        request: The request that caused the exception
        exc: The ValueError exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"ValueError on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "type": "value_error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle uncaught exceptions globally.
    
    Args:
        request: The request that caused the exception
        exc: The uncaught exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    detail = str(exc) if settings.DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "type": "internal_error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get(
    "/",
    response_model=Dict[str, Any],
    summary="Application Status",
    description="Get application status and enabled features",
    tags=["status"]
)
async def get_application_status() -> Dict[str, Any]:
    """
    Get application status and configuration summary.
    
    Returns:
        Dictionary containing application information and feature flags
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "production" if settings.is_production else "development",
        "features": {
            "vector_search": settings.ENABLE_VECTOR_SEARCH,
            "websockets": settings.ENABLE_WEBSOCKETS,
            "file_upload": settings.ENABLE_FILE_UPLOAD,
            "multi_tenant": settings.ENABLE_MULTI_TENANT
        },
        "api": {
            "version": "v1",
            "base_url": settings.API_V1_STR,
            "docs_url": f"{settings.API_V1_STR}/docs",
            "openapi_url": f"{settings.API_V1_STR}/openapi.json"
        }
    }

# Health check endpoint
@app.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health Check",
    description="Check application health status",
    tags=["status"]
)
async def health_check() -> Dict[str, Any]:
    """
    Perform health check on application and dependencies.
    
    Returns:
        Dictionary with health status and component statuses
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.perf_counter(),
        "components": {
            "api": "healthy",
            "database": "healthy",  # TODO: Add actual DB health check
            "cache": "healthy",     # TODO: Add actual cache health check
        }
    }
    
    # Add vector DB status if enabled
    if settings.ENABLE_VECTOR_SEARCH:
        health_status["components"]["vector_db"] = "healthy"  # TODO: Add actual check
    
    return health_status

# Ready check endpoint (for k8s readiness probes)
@app.get(
    "/ready",
    response_model=Dict[str, bool],
    summary="Readiness Check",
    description="Check if application is ready to serve requests",
    tags=["status"]
)
async def readiness_check() -> Dict[str, bool]:
    """
    Check if application is ready to serve requests.
    
    This endpoint is designed for Kubernetes readiness probes.
    
    Returns:
        Dictionary with readiness status
    """
    # TODO: Add actual readiness checks (DB connection, cache, etc.)
    return {"ready": True}


if __name__ == "__main__":
    """Development server entry point."""
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
    )