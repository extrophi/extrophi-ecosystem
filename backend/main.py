"""FastAPI main application."""

import os
from contextlib import asynccontextmanager

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

# Import service registry (optional - only if Consul is available)
try:
    from orchestrator.registry import ServiceRegistry
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

# Global registry and service ID for lifecycle management
registry = None
service_id = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler.

    Handles:
    - Service registration with Consul on startup
    - Database connection initialization
    - Service deregistration on shutdown
    """
    global registry, service_id

    # Startup
    print("Backend API starting...")

    # Initialize database connection pool
    # TODO: Initialize database connection pool

    # Register with Consul if available
    if REGISTRY_AVAILABLE:
        try:
            consul_host = os.getenv("CONSUL_HOST", "localhost")
            consul_port = int(os.getenv("CONSUL_PORT", "8500"))

            registry = ServiceRegistry(host=consul_host, port=consul_port)

            # Check if Consul is healthy before registering
            if registry.is_healthy():
                service_id = registry.register_service(
                    name=os.getenv("SERVICE_NAME", "backend-api"),
                    address=os.getenv("SERVICE_ADDRESS", "localhost"),
                    port=int(os.getenv("SERVICE_PORT", "8000")),
                    tags=os.getenv("SERVICE_TAGS", "api,backend").split(","),
                    health_check_interval="10s",
                    health_check_timeout="5s",
                )
                print(f"✓ Registered with Consul: {service_id}")
            else:
                print("⚠ Consul not available - running without service registry")
        except Exception as e:
            print(f"⚠ Failed to register with Consul: {e}")
            print("  Continuing without service registry...")
    else:
        print("⚠ Service registry not available - install python-consul to enable")

    # Verify all services are healthy
    # TODO: Verify all services are healthy

    yield

    # Shutdown
    print("Backend API shutting down...")

    # Deregister from Consul
    if registry and service_id:
        try:
            registry.deregister_service(service_id)
            print(f"✓ Deregistered from Consul: {service_id}")
        except Exception as e:
            print(f"⚠ Failed to deregister from Consul: {e}")

    # Close database connections
    # TODO: Close database connections


app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine with $EXTROPY token system",
    lifespan=lifespan,
)

setup_cors(app)

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
