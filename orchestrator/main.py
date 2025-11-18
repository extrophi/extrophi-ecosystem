"""Orchestrator FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .monitoring.health_checker import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global health checker instance
health_checker = HealthChecker(
    check_interval=30,  # Check every 30 seconds
    timeout=5.0,  # 5 second timeout
    failure_threshold=5,  # Open circuit after 5 failures
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Orchestrator service")
    health_checker.start()
    logger.info("Health monitoring started")

    yield

    # Shutdown
    logger.info("Shutting down Orchestrator service")
    await health_checker.stop()
    logger.info("Health monitoring stopped")


# Create FastAPI app
app = FastAPI(
    title="Orchestrator API",
    description="Service orchestration and health monitoring for Extrophi Ecosystem",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Orchestrator",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "health_status": "/health/status",
        },
    }


@app.get("/health")
async def health():
    """
    Basic health check endpoint for the orchestrator service itself.

    Returns:
        dict: Simple health status
    """
    return {"status": "ok", "service": "orchestrator"}


@app.get("/health/status")
async def health_status():
    """
    Detailed health status of all monitored services.

    Returns:
        dict: Comprehensive health status including:
            - timestamp: Current check time
            - services: Health status of each service (writer, research, backend)
            - overall_health: Aggregated system health
    """
    status = health_checker.get_status()
    return status


@app.post("/health/trigger")
async def trigger_health_check():
    """
    Manually trigger a health check of all services.

    Returns:
        dict: Updated health status
    """
    logger.info("Manual health check triggered")
    await health_checker.check_all_services()
    return health_checker.get_status()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info",
    )
