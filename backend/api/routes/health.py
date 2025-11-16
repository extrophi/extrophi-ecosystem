import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
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
