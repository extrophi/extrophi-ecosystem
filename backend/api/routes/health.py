import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": os.getenv("DATABASE_URL", "not configured"),
            "redis": os.getenv("REDIS_URL", "not configured"),
            "chromadb": f"{os.getenv('CHROMA_HOST', 'chromadb')}:"
            f"{os.getenv('CHROMA_PORT', '8000')}",
        },
    }
