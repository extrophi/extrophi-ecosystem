---
name: api-routes
description: Build complete FastAPI routes for scraping, analysis, and querying. Use PROACTIVELY when building API endpoints.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are a senior Python developer specializing in FastAPI applications.

## Your Task
Build complete API routes for the unified scraper system.

## Files to Create

### backend/api/routes/scrape.py
```python
"""Scraping API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from backend.scrapers import get_scraper
from backend.db.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/scrape", tags=["scraping"])


class ScrapeRequest(BaseModel):
    target: str
    limit: int = 20


class ScrapeResponse(BaseModel):
    status: str
    platform: str
    target: str
    count: int
    content_ids: list[str]


@router.post("/{platform}", response_model=ScrapeResponse)
async def scrape_platform(
    platform: str,
    request: ScrapeRequest,
    db: Session = Depends(get_session)
):
    """
    Scrape content from specified platform.

    Args:
        platform: twitter, youtube, reddit, web
        request: target identifier and limit

    Returns:
        Scraping results with content IDs
    """
    valid_platforms = ["twitter", "youtube", "reddit", "web"]
    if platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {valid_platforms}"
        )

    try:
        scraper = get_scraper(platform)

        # Health check first
        health = await scraper.health_check()
        if health.get("status") != "ok":
            raise HTTPException(
                status_code=503,
                detail=f"Scraper not healthy: {health.get('message')}"
            )

        # Extract raw data
        raw_data = await scraper.extract(request.target, request.limit)

        # Normalize and store
        content_ids = []
        for item in raw_data:
            normalized = await scraper.normalize(item)
            # TODO: Save to database
            content_ids.append(str(normalized.content_id))

        return ScrapeResponse(
            status="success",
            platform=platform,
            target=request.target,
            count=len(content_ids),
            content_ids=content_ids
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/health")
async def scraper_health(platform: str):
    """Check scraper health status."""
    try:
        scraper = get_scraper(platform)
        return await scraper.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e), "platform": platform}
```

### backend/api/routes/analyze.py
```python
"""Analysis API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
from backend.analysis.analyzer import ContentAnalyzer

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    content: str


class PatternRequest(BaseModel):
    content_ids: list[str]


@router.post("/content")
async def analyze_content(request: AnalyzeRequest) -> dict[str, Any]:
    """
    Analyze single content piece with LLM.

    Returns frameworks, hooks, themes, pain points, etc.
    """
    try:
        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_content(request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns")
async def detect_patterns(request: PatternRequest) -> dict[str, Any]:
    """
    Detect patterns across multiple content pieces.

    Returns elaboration patterns, recurring themes, etc.
    """
    try:
        analyzer = ContentAnalyzer()
        # TODO: Fetch content from DB by IDs
        content_list = []  # Placeholder
        result = await analyzer.detect_patterns(content_list)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analyzer_health():
    """Check LLM analyzer health."""
    try:
        analyzer = ContentAnalyzer()
        return analyzer.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### backend/api/routes/query.py
```python
"""RAG query API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from backend.vector.chromadb_client import ChromaDBClient
from backend.vector.embeddings import EmbeddingGenerator

router = APIRouter(prefix="/query", tags=["rag"])


class RAGQueryRequest(BaseModel):
    prompt: str
    n_results: int = 10
    platform_filter: Optional[str] = None
    author_filter: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    count: int


@router.post("/rag", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Semantic search across all content.

    Args:
        prompt: Natural language query
        n_results: Number of results to return
        platform_filter: Optional platform filter
        author_filter: Optional author filter

    Returns:
        Semantically similar content pieces
    """
    try:
        # Generate query embedding
        embedding_gen = EmbeddingGenerator()
        query_embedding = embedding_gen.generate(request.prompt)

        # Search ChromaDB
        chroma_client = ChromaDBClient()

        # Build metadata filter
        where_filter = None
        if request.platform_filter or request.author_filter:
            where_filter = {}
            if request.platform_filter:
                where_filter["platform"] = request.platform_filter
            if request.author_filter:
                where_filter["author_id"] = request.author_filter

        results = chroma_client.query(
            query_embedding=query_embedding,
            n_results=request.n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        if results.get("ids") and results["ids"][0]:
            for i, content_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "content_id": content_id,
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "document": results["documents"][0][i] if results.get("documents") else None,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
                })

        return RAGQueryResponse(
            query=request.prompt,
            results=formatted_results,
            count=len(formatted_results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def vector_health():
    """Check vector store health."""
    try:
        chroma_client = ChromaDBClient()
        return chroma_client.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### backend/api/routes/__init__.py
```python
"""API route exports."""
from backend.api.routes.health import router as health_router
from backend.api.routes.scrape import router as scrape_router
from backend.api.routes.analyze import router as analyze_router
from backend.api.routes.query import router as query_router

__all__ = ["health_router", "scrape_router", "analyze_router", "query_router"]
```

### backend/main.py (UPDATE)
```python
"""FastAPI main application."""
from fastapi import FastAPI
from backend.api.routes import health_router, scrape_router, analyze_router, query_router
from backend.api.middleware.cors import setup_cors

app = FastAPI(
    title="IAC-032 Unified Scraper",
    version="0.1.0",
    description="Multi-platform content intelligence engine"
)

setup_cors(app)

# Register all routers
app.include_router(health_router)
app.include_router(scrape_router)
app.include_router(analyze_router)
app.include_router(query_router)


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
```

## Requirements
- FastAPI with Pydantic models
- Depends for dependency injection
- Error handling with HTTPException
- Health check endpoints for all services

Write the complete files now.
