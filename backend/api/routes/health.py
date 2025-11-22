import os

from fastapi import APIRouter

from backend.db.connection import health_check as db_health_check
from backend.queue.redis_queue import get_queue

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Checks connectivity to:
    - PostgreSQL database
    - Redis queue
    - ChromaDB (config only)
    """
    # Check database
    db_healthy = db_health_check()

    # Check Redis
    queue = get_queue()
    redis_healthy = queue.health_check()
    queue_length = queue.get_queue_length() if redis_healthy else 0

    # Overall status
    status = "healthy" if (db_healthy and redis_healthy) else "degraded"

    chroma_host = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port = os.getenv("CHROMA_PORT", "8000")

    return {
        "status": status,
        "services": {
            "database": {
                "status": "up" if db_healthy else "down",
                "url": os.getenv("DATABASE_URL", "not configured"),
            },
            "redis": {
                "status": "up" if redis_healthy else "down",
                "url": os.getenv("REDIS_URL", "not configured"),
                "queue_length": queue_length,
            },
            "chromadb": {
                "status": "configured",
                "url": f"{chroma_host}:{chroma_port}",
            },
        },
    }
