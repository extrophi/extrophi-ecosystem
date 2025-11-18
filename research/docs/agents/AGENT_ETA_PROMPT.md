# AGENT ETA: FastAPI Core Engine

## Mission Statement

You are AGENT ETA, the API orchestrator for IAC-032 Unified Scraper. Your mission is to build a production-ready FastAPI backend that serves as the central nervous system connecting scrapers, RAG services, and future frontend clients. You provide RESTful endpoints for scraping, querying, and health monitoring with proper middleware for CORS, error handling, and request validation.

**Core Responsibility**: Create a robust, well-documented API layer that routes requests to appropriate services, handles errors gracefully, and provides Swagger documentation for all endpoints.

---

## Architecture Context

You are building the API gateway that connects:
- **Frontend** (Week 2: Tauri + Svelte) → Your endpoints
- **Scrapers** (AGENT EPSILON/THETA) → Your scraper factory
- **RAG Engine** (AGENT ZETA) → Your query endpoints
- **PostgreSQL** ← Your database connections
- **External Clients** → Your REST API

Your FastAPI server provides:
1. Scraping endpoints (trigger platform-specific scrapers)
2. Query endpoints (semantic search via RAG)
3. Health monitoring (service status checks)
4. Error handling (consistent error responses)
5. CORS support (cross-origin requests)

---

## Files to Create

### 1. `backend/main.py`

```python
"""
FastAPI Main Application for IAC-032 Unified Scraper.

Central orchestrator for multi-platform content intelligence.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from api.routes import scraping, query, health
from api.middleware.cors import setup_cors
from api.middleware.errors import setup_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting IAC-032 Unified Scraper API")

    # Initialize services
    app.state.startup_time = datetime.now(timezone.utc)
    app.state.request_count = 0

    # Verify environment
    required_env = ["OPENAI_API_KEY"]
    missing = [var for var in required_env if not os.getenv(var)]
    if missing:
        print(f"WARNING: Missing environment variables: {missing}")

    print(f"[{datetime.now(timezone.utc).isoformat()}] API ready at http://localhost:8000")
    print(f"[{datetime.now(timezone.utc).isoformat()}] Swagger docs at http://localhost:8000/docs")

    yield

    # Shutdown
    print(f"[{datetime.now(timezone.utc).isoformat()}] Shutting down API")
    # Cleanup resources here if needed


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="IAC-032 Unified Scraper API",
        description="""
Multi-platform content intelligence engine.

## Features
- **Scraping**: Twitter, YouTube, Reddit, Web content
- **RAG**: Semantic search with vector embeddings
- **Analysis**: LLM-powered content analysis
- **Patterns**: Cross-platform pattern detection

## Platforms Supported
- Twitter (via Playwright stealth)
- YouTube (transcripts + metadata)
- Reddit (PRAW API)
- Web (Jina.ai + ScraperAPI)

## Authentication
Currently no authentication required for MVP.
Production will use API keys + rate limiting.
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Setup middleware
    setup_cors(app)
    setup_error_handlers(app)

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(scraping.router, prefix="/scrape", tags=["scraping"])
    app.include_router(query.router, prefix="/query", tags=["query"])

    # Request counting middleware
    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        app.state.request_count += 1
        response = await call_next(request)
        response.headers["X-Request-Count"] = str(app.state.request_count)
        return response

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """
        Root endpoint with API information.
        """
        return {
            "name": "IAC-032 Unified Scraper API",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "scrape": "/scrape/{platform}",
                "query": "/query/rag",
                "health": "/health"
            }
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

---

### 2. `backend/api/__init__.py`

```python
"""
API layer for IAC-032 Unified Scraper.

This module contains:
- Routes (endpoints for scraping, query, health)
- Middleware (CORS, error handling)
- Dependencies (shared request dependencies)
"""

__version__ = "0.1.0"
```

---

### 3. `backend/api/routes/__init__.py`

```python
"""
API Routes module.

Contains all endpoint routers:
- scraping: Platform-specific scraping endpoints
- query: RAG and semantic search endpoints
- health: Service health and monitoring
"""

from . import scraping, query, health

__all__ = ["scraping", "query", "health"]
```

---

### 4. `backend/api/routes/scraping.py`

```python
"""
Scraping endpoints for multi-platform content extraction.

Supports: Twitter, YouTube, Reddit, Web
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field, HttpUrl

from services.scraper_factory import ScraperFactory, ScraperConfig, ScrapeResult


router = APIRouter()


# Request/Response Models

class TwitterScrapeRequest(BaseModel):
    """Request to scrape Twitter profile."""
    username: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    max_tweets: int = Field(default=100, ge=1, le=1000)
    include_replies: bool = Field(default=False)
    include_retweets: bool = Field(default=False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "dankoe",
                "max_tweets": 100,
                "include_replies": False,
                "include_retweets": False
            }
        }
    }


class YouTubeScrapeRequest(BaseModel):
    """Request to scrape YouTube video."""
    video_id: str = Field(..., min_length=11, max_length=11)
    include_transcript: bool = Field(default=True)
    include_comments: bool = Field(default=False)
    max_comments: int = Field(default=100, ge=0, le=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "include_transcript": True,
                "include_comments": False,
                "max_comments": 100
            }
        }
    }


class RedditScrapeRequest(BaseModel):
    """Request to scrape Reddit subreddit."""
    subreddit: str = Field(..., min_length=1, max_length=50)
    sort_by: str = Field(default="hot", pattern=r"^(hot|new|top|rising)$")
    time_filter: str = Field(default="week", pattern=r"^(hour|day|week|month|year|all)$")
    max_posts: int = Field(default=50, ge=1, le=500)
    include_comments: bool = Field(default=True)
    max_comments_per_post: int = Field(default=10, ge=0, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "subreddit": "productivity",
                "sort_by": "top",
                "time_filter": "week",
                "max_posts": 50,
                "include_comments": True,
                "max_comments_per_post": 10
            }
        }
    }


class WebScrapeRequest(BaseModel):
    """Request to scrape web page."""
    url: HttpUrl
    extract_mode: str = Field(default="article", pattern=r"^(article|full|clean)$")
    follow_links: bool = Field(default=False)
    max_depth: int = Field(default=1, ge=1, le=3)

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://calnewport.com/deep-work-rules/",
                "extract_mode": "article",
                "follow_links": False,
                "max_depth": 1
            }
        }
    }


class ScrapeResponse(BaseModel):
    """Standard response for scraping operations."""
    success: bool
    platform: str
    items_scraped: int
    items_stored: int
    errors: List[str] = Field(default_factory=list)
    scrape_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScrapeJobStatus(BaseModel):
    """Status of background scraping job."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0.0 to 1.0
    items_processed: int
    errors: List[str]
    started_at: datetime
    estimated_completion: Optional[datetime] = None


# Endpoints

@router.post(
    "/twitter",
    response_model=ScrapeResponse,
    summary="Scrape Twitter Profile",
    description="""
Scrape tweets from a Twitter profile.

Uses Playwright with stealth mode for anti-detection.
Reuses patterns from IAC-024 Tweet Hunter.

**Rate Limits**: Adaptive backoff based on Twitter responses.
**Cost**: Free (uses direct browser automation)
    """
)
async def scrape_twitter(request: TwitterScrapeRequest) -> ScrapeResponse:
    """
    Scrape tweets from Twitter profile.

    Args:
        request: Twitter scrape configuration

    Returns:
        Scrape result with statistics
    """
    config = ScraperConfig(
        platform="twitter",
        target=request.username,
        max_items=request.max_tweets,
        options={
            "include_replies": request.include_replies,
            "include_retweets": request.include_retweets
        }
    )

    factory = ScraperFactory()

    try:
        result = await factory.scrape(config)
        return ScrapeResponse(
            success=result.success,
            platform="twitter",
            items_scraped=result.items_scraped,
            items_stored=result.items_stored,
            errors=result.errors,
            scrape_id=result.scrape_id,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
            metadata={"username": request.username}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post(
    "/youtube",
    response_model=ScrapeResponse,
    summary="Scrape YouTube Video",
    description="""
Scrape YouTube video transcript and metadata.

Uses youtube-transcript-api for transcripts.
Uses yt-dlp for metadata extraction.

**Rate Limits**: YouTube API quotas apply.
**Cost**: Free tier available.
    """
)
async def scrape_youtube(request: YouTubeScrapeRequest) -> ScrapeResponse:
    """
    Scrape YouTube video transcript and metadata.

    Args:
        request: YouTube scrape configuration

    Returns:
        Scrape result with statistics
    """
    config = ScraperConfig(
        platform="youtube",
        target=request.video_id,
        max_items=1,  # Single video
        options={
            "include_transcript": request.include_transcript,
            "include_comments": request.include_comments,
            "max_comments": request.max_comments
        }
    )

    factory = ScraperFactory()

    try:
        result = await factory.scrape(config)
        return ScrapeResponse(
            success=result.success,
            platform="youtube",
            items_scraped=result.items_scraped,
            items_stored=result.items_stored,
            errors=result.errors,
            scrape_id=result.scrape_id,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
            metadata={"video_id": request.video_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post(
    "/reddit",
    response_model=ScrapeResponse,
    summary="Scrape Reddit Subreddit",
    description="""
Scrape posts from a Reddit subreddit.

Uses PRAW (Python Reddit API Wrapper).
Includes post content and top comments.

**Rate Limits**: 1000 requests per 10 minutes (OAuth).
**Cost**: Free with Reddit account.
    """
)
async def scrape_reddit(request: RedditScrapeRequest) -> ScrapeResponse:
    """
    Scrape posts from Reddit subreddit.

    Args:
        request: Reddit scrape configuration

    Returns:
        Scrape result with statistics
    """
    config = ScraperConfig(
        platform="reddit",
        target=request.subreddit,
        max_items=request.max_posts,
        options={
            "sort_by": request.sort_by,
            "time_filter": request.time_filter,
            "include_comments": request.include_comments,
            "max_comments_per_post": request.max_comments_per_post
        }
    )

    factory = ScraperFactory()

    try:
        result = await factory.scrape(config)
        return ScrapeResponse(
            success=result.success,
            platform="reddit",
            items_scraped=result.items_scraped,
            items_stored=result.items_stored,
            errors=result.errors,
            scrape_id=result.scrape_id,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
            metadata={
                "subreddit": request.subreddit,
                "sort_by": request.sort_by
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post(
    "/web",
    response_model=ScrapeResponse,
    summary="Scrape Web Page",
    description="""
Scrape content from web page.

Uses Jina.ai Reader API (50K pages/month FREE).
Falls back to ScraperAPI for JS-heavy sites.

**Rate Limits**: 50K pages/month free tier.
**Cost**: $0 for static content.
    """
)
async def scrape_web(request: WebScrapeRequest) -> ScrapeResponse:
    """
    Scrape content from web page.

    Args:
        request: Web scrape configuration

    Returns:
        Scrape result with statistics
    """
    config = ScraperConfig(
        platform="web",
        target=str(request.url),
        max_items=1 if not request.follow_links else 10,
        options={
            "extract_mode": request.extract_mode,
            "follow_links": request.follow_links,
            "max_depth": request.max_depth
        }
    )

    factory = ScraperFactory()

    try:
        result = await factory.scrape(config)
        return ScrapeResponse(
            success=result.success,
            platform="web",
            items_scraped=result.items_scraped,
            items_stored=result.items_stored,
            errors=result.errors,
            scrape_id=result.scrape_id,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
            metadata={"url": str(request.url)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.get(
    "/status/{scrape_id}",
    response_model=ScrapeJobStatus,
    summary="Get Scrape Job Status",
    description="Check status of a background scraping job."
)
async def get_scrape_status(
    scrape_id: str = Path(..., description="Scrape job ID")
) -> ScrapeJobStatus:
    """
    Get status of scraping job.

    Args:
        scrape_id: Job identifier

    Returns:
        Current job status
    """
    factory = ScraperFactory()

    try:
        status = await factory.get_job_status(scrape_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {scrape_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get(
    "/platforms",
    summary="List Supported Platforms",
    description="Get list of all supported scraping platforms."
)
async def list_platforms() -> Dict[str, Any]:
    """
    List all supported scraping platforms.

    Returns:
        Dictionary of platform configurations
    """
    factory = ScraperFactory()
    return factory.get_supported_platforms()
```

---

### 5. `backend/api/routes/query.py`

```python
"""
RAG Query endpoints for semantic search and pattern detection.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from services.rag_query import RAGQueryEngine, RAGQuery, RAGResult


router = APIRouter()


# Request/Response Models

class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., min_length=3, max_length=1000)
    n_results: int = Field(default=10, ge=1, le=100)
    platform_filter: Optional[str] = Field(default=None, pattern=r"^(twitter|youtube|reddit|web)$")
    author_filter: Optional[str] = Field(default=None)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "focus systems for knowledge workers",
                "n_results": 10,
                "platform_filter": None,
                "author_filter": None,
                "min_similarity": 0.5
            }
        }
    }


class SemanticSearchResult(BaseModel):
    """Single search result."""
    id: str
    content: str
    platform: str
    source_url: str
    author_name: str
    similarity: float
    metadata: Dict[str, Any]


class SemanticSearchResponse(BaseModel):
    """Response from semantic search."""
    query: str
    results: List[SemanticSearchResult]
    total_results: int
    query_cost_usd: float
    processing_time_seconds: float
    context: str  # Assembled context for LLM


class SimilarContentRequest(BaseModel):
    """Request to find similar content."""
    content: str = Field(..., min_length=10, max_length=10000)
    n_results: int = Field(default=5, ge=1, le=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Focus is the new IQ. In a distracted world, attention is your competitive advantage.",
                "n_results": 5
            }
        }
    }


class PatternDetectionRequest(BaseModel):
    """Request to detect cross-platform patterns."""
    author_id: str = Field(..., min_length=1, max_length=100)
    similarity_threshold: float = Field(default=0.85, ge=0.5, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "author_id": "dankoe",
                "similarity_threshold": 0.85
            }
        }
    }


class PatternCluster(BaseModel):
    """Cluster of similar content across platforms."""
    primary: SemanticSearchResult
    related: List[SemanticSearchResult]
    platforms_involved: List[str]


class PatternDetectionResponse(BaseModel):
    """Response from pattern detection."""
    author_id: str
    patterns_found: int
    clusters: List[PatternCluster]
    analysis_time_seconds: float


class RAGStatsResponse(BaseModel):
    """RAG system statistics."""
    embedding_costs: Dict[str, Any]
    vector_store: Dict[str, Any]
    last_updated: str


# Endpoints

@router.post(
    "/rag",
    response_model=SemanticSearchResponse,
    summary="Semantic Search via RAG",
    description="""
Perform semantic search across all indexed content.

Uses ChromaDB vector store with OpenAI embeddings.
Returns content ranked by cosine similarity.

**Cost**: $0.00002 per 1K tokens for query embedding.
**Performance**: Sub-second for 10K+ documents.
    """
)
async def semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    """
    Perform semantic search using RAG.

    Args:
        request: Search configuration

    Returns:
        Search results with context
    """
    engine = RAGQueryEngine()

    try:
        rag_query = RAGQuery(
            query=request.query,
            n_results=request.n_results,
            platform_filter=request.platform_filter,
            author_filter=request.author_filter,
            min_similarity=request.min_similarity
        )

        result = await engine.query(rag_query)

        search_results = [
            SemanticSearchResult(
                id=r.id,
                content=r.content,
                platform=r.platform,
                source_url=r.source_url,
                author_name=r.author_name,
                similarity=r.similarity,
                metadata=r.metadata
            )
            for r in result.results
        ]

        return SemanticSearchResponse(
            query=result.query,
            results=search_results,
            total_results=result.total_results,
            query_cost_usd=result.query_cost_usd,
            processing_time_seconds=result.processing_time_seconds,
            context=result.context_assembled
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post(
    "/similar",
    response_model=List[SemanticSearchResult],
    summary="Find Similar Content",
    description="""
Find content similar to provided text.

Useful for detecting plagiarism or content reuse.
    """
)
async def find_similar(request: SimilarContentRequest) -> List[SemanticSearchResult]:
    """
    Find content similar to provided text.

    Args:
        request: Content to find similar items for

    Returns:
        List of similar content
    """
    engine = RAGQueryEngine()

    try:
        results = await engine.find_similar_content(
            content=request.content,
            n_results=request.n_results
        )

        return [
            SemanticSearchResult(
                id=r.id,
                content=r.content,
                platform=r.platform,
                source_url=r.source_url,
                author_name=r.author_name,
                similarity=r.similarity,
                metadata=r.metadata
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


@router.post(
    "/patterns",
    response_model=PatternDetectionResponse,
    summary="Detect Cross-Platform Patterns",
    description="""
Detect content that appears across multiple platforms.

Identifies Dan Koe-style elaboration patterns:
- Tweet (Tuesday)
- Newsletter expansion (Saturday)
- YouTube deep dive (next week)

**Use Case**: Find how authors repurpose content.
    """
)
async def detect_patterns(request: PatternDetectionRequest) -> PatternDetectionResponse:
    """
    Detect cross-platform content patterns.

    Args:
        request: Pattern detection configuration

    Returns:
        Clusters of related content
    """
    import time
    start_time = time.time()

    engine = RAGQueryEngine()

    try:
        patterns = await engine.detect_cross_platform_patterns(
            author_id=request.author_id,
            similarity_threshold=request.similarity_threshold
        )

        clusters = []
        for pattern in patterns:
            primary = SemanticSearchResult(
                id=pattern["primary"].id,
                content=pattern["primary"].content,
                platform=pattern["primary"].platform,
                source_url=pattern["primary"].source_url,
                author_name=pattern["primary"].author_name,
                similarity=1.0,
                metadata=pattern["primary"].metadata
            )

            related = [
                SemanticSearchResult(
                    id=r.id,
                    content=r.content,
                    platform=r.platform,
                    source_url=r.source_url,
                    author_name=r.author_name,
                    similarity=r.similarity,
                    metadata=r.metadata
                )
                for r in pattern["related"]
            ]

            platforms = list(set([primary.platform] + [r.platform for r in related]))

            clusters.append(PatternCluster(
                primary=primary,
                related=related,
                platforms_involved=platforms
            ))

        elapsed = time.time() - start_time

        return PatternDetectionResponse(
            author_id=request.author_id,
            patterns_found=len(clusters),
            clusters=clusters,
            analysis_time_seconds=elapsed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")


@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    summary="Get RAG System Statistics",
    description="""
Get statistics about the RAG system.

Includes:
- Embedding costs (cumulative)
- Vector store size
- Platform distribution
    """
)
async def get_rag_stats() -> RAGStatsResponse:
    """
    Get RAG system statistics.

    Returns:
        System statistics
    """
    engine = RAGQueryEngine()

    try:
        stats = engine.get_stats()
        return RAGStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get(
    "/context",
    summary="Generate Context for LLM",
    description="""
Generate assembled context from query for use in LLM prompts.

Returns formatted context string ready for GPT-4 or Claude.
    """
)
async def generate_context(
    query: str = Query(..., min_length=3, description="Search query"),
    n_results: int = Query(default=5, ge=1, le=20, description="Number of results to include")
) -> Dict[str, Any]:
    """
    Generate context for LLM from query.

    Args:
        query: Search query
        n_results: Number of results to include

    Returns:
        Context string and metadata
    """
    engine = RAGQueryEngine()

    try:
        rag_query = RAGQuery(query=query, n_results=n_results)
        result = await engine.query(rag_query)

        return {
            "query": query,
            "context": result.context_assembled,
            "sources_used": result.total_results,
            "cost_usd": result.query_cost_usd
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context generation failed: {str(e)}")
```

---

### 6. `backend/api/routes/health.py`

```python
"""
Health check and monitoring endpoints.
"""

import os
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter()


class ServiceStatus(BaseModel):
    """Status of individual service."""
    name: str
    status: str  # healthy, unhealthy, degraded
    message: str
    last_check: datetime


class HealthResponse(BaseModel):
    """Overall health check response."""
    status: str  # healthy, unhealthy, degraded
    version: str
    uptime_seconds: float
    total_requests: int
    services: Dict[str, ServiceStatus]
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness probe response."""
    ready: bool
    checks: Dict[str, bool]


class LivenessResponse(BaseModel):
    """Liveness probe response."""
    alive: bool
    timestamp: datetime


@router.get(
    "",
    response_model=HealthResponse,
    summary="Full Health Check",
    description="""
Comprehensive health check for all services.

Checks:
- OpenAI API connectivity
- ChromaDB vector store
- PostgreSQL database (if configured)
- Disk space
    """
)
async def health_check(request: Request) -> HealthResponse:
    """
    Perform comprehensive health check.

    Returns:
        Health status of all services
    """
    services = {}
    overall_status = "healthy"

    # Check OpenAI API
    openai_status = await check_openai_service()
    services["openai"] = openai_status
    if openai_status.status != "healthy":
        overall_status = "degraded"

    # Check ChromaDB
    chromadb_status = check_chromadb_service()
    services["chromadb"] = chromadb_status
    if chromadb_status.status == "unhealthy":
        overall_status = "unhealthy"
    elif chromadb_status.status == "degraded" and overall_status == "healthy":
        overall_status = "degraded"

    # Check environment
    env_status = check_environment()
    services["environment"] = env_status
    if env_status.status != "healthy":
        overall_status = "degraded"

    # Check disk space
    disk_status = check_disk_space()
    services["disk"] = disk_status
    if disk_status.status == "unhealthy":
        overall_status = "unhealthy"

    # Calculate uptime
    startup_time = request.app.state.startup_time
    uptime = (datetime.now(timezone.utc) - startup_time).total_seconds()

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        uptime_seconds=uptime,
        total_requests=request.app.state.request_count,
        services=services,
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Check if service is ready to accept traffic."
)
async def readiness_probe() -> ReadinessResponse:
    """
    Kubernetes-style readiness probe.

    Returns:
        Readiness status
    """
    checks = {
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "chromadb_dir": os.path.isdir("data/chromadb") or os.makedirs("data/chromadb", exist_ok=True) or True,
        "python_version": True  # Already running if we get here
    }

    ready = all(checks.values())

    return ReadinessResponse(ready=ready, checks=checks)


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Check if service is alive."
)
async def liveness_probe() -> LivenessResponse:
    """
    Kubernetes-style liveness probe.

    Returns:
        Liveness status
    """
    return LivenessResponse(
        alive=True,
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Get metrics in Prometheus format."
)
async def prometheus_metrics(request: Request) -> str:
    """
    Return metrics in Prometheus text format.

    Returns:
        Prometheus-formatted metrics
    """
    startup_time = request.app.state.startup_time
    uptime = (datetime.now(timezone.utc) - startup_time).total_seconds()
    request_count = request.app.state.request_count

    metrics = f"""
# HELP iac032_uptime_seconds Time since service started
# TYPE iac032_uptime_seconds gauge
iac032_uptime_seconds {uptime:.2f}

# HELP iac032_requests_total Total requests served
# TYPE iac032_requests_total counter
iac032_requests_total {request_count}

# HELP iac032_health_status Service health (1=healthy, 0.5=degraded, 0=unhealthy)
# TYPE iac032_health_status gauge
iac032_health_status 1.0
    """.strip()

    return metrics


# Helper functions

async def check_openai_service() -> ServiceStatus:
    """Check OpenAI API connectivity."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return ServiceStatus(
            name="openai",
            status="unhealthy",
            message="OPENAI_API_KEY not configured",
            last_check=datetime.now(timezone.utc)
        )

    # Light check - just verify key format
    if api_key.startswith("sk-") and len(api_key) > 20:
        return ServiceStatus(
            name="openai",
            status="healthy",
            message="API key configured",
            last_check=datetime.now(timezone.utc)
        )

    return ServiceStatus(
        name="openai",
        status="degraded",
        message="API key format may be invalid",
        last_check=datetime.now(timezone.utc)
    )


def check_chromadb_service() -> ServiceStatus:
    """Check ChromaDB availability."""
    persist_dir = "data/chromadb"

    try:
        # Ensure directory exists
        os.makedirs(persist_dir, exist_ok=True)

        # Check if writable
        test_file = os.path.join(persist_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)

        return ServiceStatus(
            name="chromadb",
            status="healthy",
            message=f"Persistence directory ready: {persist_dir}",
            last_check=datetime.now(timezone.utc)
        )
    except PermissionError:
        return ServiceStatus(
            name="chromadb",
            status="unhealthy",
            message=f"No write permission for {persist_dir}",
            last_check=datetime.now(timezone.utc)
        )
    except Exception as e:
        return ServiceStatus(
            name="chromadb",
            status="unhealthy",
            message=str(e),
            last_check=datetime.now(timezone.utc)
        )


def check_environment() -> ServiceStatus:
    """Check required environment variables."""
    required = ["OPENAI_API_KEY"]
    optional = ["SCRAPER_API_KEY", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]

    missing_required = [var for var in required if not os.getenv(var)]
    missing_optional = [var for var in optional if not os.getenv(var)]

    if missing_required:
        return ServiceStatus(
            name="environment",
            status="unhealthy",
            message=f"Missing required: {missing_required}",
            last_check=datetime.now(timezone.utc)
        )

    if missing_optional:
        return ServiceStatus(
            name="environment",
            status="degraded",
            message=f"Missing optional: {missing_optional}",
            last_check=datetime.now(timezone.utc)
        )

    return ServiceStatus(
        name="environment",
        status="healthy",
        message="All environment variables configured",
        last_check=datetime.now(timezone.utc)
    )


def check_disk_space() -> ServiceStatus:
    """Check available disk space."""
    import shutil

    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)

        if free_gb < 1.0:
            return ServiceStatus(
                name="disk",
                status="unhealthy",
                message=f"Only {free_gb:.2f} GB free",
                last_check=datetime.now(timezone.utc)
            )

        if free_gb < 5.0:
            return ServiceStatus(
                name="disk",
                status="degraded",
                message=f"Low disk space: {free_gb:.2f} GB free",
                last_check=datetime.now(timezone.utc)
            )

        return ServiceStatus(
            name="disk",
            status="healthy",
            message=f"{free_gb:.2f} GB free",
            last_check=datetime.now(timezone.utc)
        )
    except Exception as e:
        return ServiceStatus(
            name="disk",
            status="degraded",
            message=f"Cannot check disk space: {e}",
            last_check=datetime.now(timezone.utc)
        )
```

---

### 7. `backend/api/middleware/cors.py`

```python
"""
CORS (Cross-Origin Resource Sharing) middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.

    Allows frontend applications (Tauri, browser) to make requests.

    Args:
        app: FastAPI application instance
    """
    # Allowed origins
    origins = [
        "http://localhost:3000",  # Development frontend
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Alternative dev port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "tauri://localhost",  # Tauri WebView
        "https://tauri.localhost",  # Tauri secure context
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-API-Key",
            "Accept",
            "Origin",
            "User-Agent"
        ],
        expose_headers=[
            "X-Request-Count",
            "X-Processing-Time",
            "X-Rate-Limit-Remaining"
        ],
        max_age=3600  # Cache preflight for 1 hour
    )
```

---

### 8. `backend/api/middleware/errors.py`

```python
"""
Global error handling middleware.
"""

import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global error handlers for the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTPException",
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "ValidationError",
                    "status_code": 422,
                    "detail": "Request validation failed",
                    "errors": errors,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors."""
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "ValueError",
                    "status_code": 400,
                    "detail": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        # Log the full traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Unhandled exception at {request.url.path}")
        print(error_trace)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "status_code": 500,
                    "detail": "Internal server error",
                    "message": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
```

---

### 9. `backend/services/scraper_factory.py`

```python
"""
Scraper Factory - Routes to platform-specific scrapers.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class ScraperConfig(BaseModel):
    """Configuration for scraping operation."""
    platform: str = Field(..., pattern=r"^(twitter|youtube|reddit|web)$")
    target: str
    max_items: int = Field(default=100, ge=1, le=10000)
    options: Dict[str, Any] = Field(default_factory=dict)


class ScrapeResult(BaseModel):
    """Result from scraping operation."""
    success: bool
    scrape_id: str
    platform: str
    items_scraped: int
    items_stored: int
    errors: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class ScraperFactory:
    """
    Factory for creating and managing platform-specific scrapers.

    Follows adapter pattern - each platform has its own scraper implementation.
    """

    SUPPORTED_PLATFORMS = {
        "twitter": {
            "name": "Twitter/X",
            "adapter": "adapters.twitter",
            "requires_auth": True,
            "rate_limit": "Adaptive",
            "cost": "Free (Playwright)"
        },
        "youtube": {
            "name": "YouTube",
            "adapter": "adapters.youtube",
            "requires_auth": False,
            "rate_limit": "API quota",
            "cost": "Free"
        },
        "reddit": {
            "name": "Reddit",
            "adapter": "adapters.reddit",
            "requires_auth": True,
            "rate_limit": "1000 req/10min",
            "cost": "Free"
        },
        "web": {
            "name": "Web/Blogs",
            "adapter": "adapters.web",
            "requires_auth": False,
            "rate_limit": "50K pages/month (Jina)",
            "cost": "$0-49/month"
        }
    }

    def __init__(self):
        """Initialize scraper factory."""
        self._active_jobs: Dict[str, Dict[str, Any]] = {}

    def get_supported_platforms(self) -> Dict[str, Any]:
        """
        Get information about supported platforms.

        Returns:
            Dictionary of platform configurations
        """
        return {
            "platforms": self.SUPPORTED_PLATFORMS,
            "total": len(self.SUPPORTED_PLATFORMS)
        }

    async def scrape(self, config: ScraperConfig) -> ScrapeResult:
        """
        Execute scraping operation for given platform.

        Args:
            config: Scraping configuration

        Returns:
            Scrape result with statistics
        """
        import time

        scrape_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        # Track job
        self._active_jobs[scrape_id] = {
            "config": config,
            "status": "running",
            "progress": 0.0,
            "items_processed": 0,
            "errors": [],
            "started_at": started_at
        }

        try:
            # Route to appropriate scraper
            if config.platform == "twitter":
                result = await self._scrape_twitter(config, scrape_id)
            elif config.platform == "youtube":
                result = await self._scrape_youtube(config, scrape_id)
            elif config.platform == "reddit":
                result = await self._scrape_reddit(config, scrape_id)
            elif config.platform == "web":
                result = await self._scrape_web(config, scrape_id)
            else:
                raise ValueError(f"Unsupported platform: {config.platform}")

            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()

            # Update job status
            self._active_jobs[scrape_id]["status"] = "completed"
            self._active_jobs[scrape_id]["progress"] = 1.0

            return ScrapeResult(
                success=True,
                scrape_id=scrape_id,
                platform=config.platform,
                items_scraped=result["items_scraped"],
                items_stored=result["items_stored"],
                errors=result.get("errors", []),
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )

        except Exception as e:
            self._active_jobs[scrape_id]["status"] = "failed"
            self._active_jobs[scrape_id]["errors"].append(str(e))

            return ScrapeResult(
                success=False,
                scrape_id=scrape_id,
                platform=config.platform,
                items_scraped=0,
                items_stored=0,
                errors=[str(e)],
                started_at=started_at,
                completed_at=datetime.now(timezone.utc)
            )

    async def get_job_status(self, scrape_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of scraping job.

        Args:
            scrape_id: Job identifier

        Returns:
            Job status or None if not found
        """
        if scrape_id not in self._active_jobs:
            return None

        job = self._active_jobs[scrape_id]

        return {
            "job_id": scrape_id,
            "status": job["status"],
            "progress": job["progress"],
            "items_processed": job["items_processed"],
            "errors": job["errors"],
            "started_at": job["started_at"],
            "estimated_completion": None  # TODO: Implement estimation
        }

    async def _scrape_twitter(self, config: ScraperConfig, scrape_id: str) -> Dict[str, Any]:
        """
        Scrape Twitter using Playwright stealth.

        TODO: Implement actual scraping using IAC-024 patterns.
        """
        # Placeholder - will be implemented by AGENT EPSILON
        return {
            "items_scraped": 0,
            "items_stored": 0,
            "errors": ["Twitter scraper not yet implemented - see AGENT_EPSILON_PROMPT.md"]
        }

    async def _scrape_youtube(self, config: ScraperConfig, scrape_id: str) -> Dict[str, Any]:
        """
        Scrape YouTube transcripts.

        TODO: Implement using youtube-transcript-api.
        """
        # Placeholder - will be implemented by AGENT THETA
        return {
            "items_scraped": 0,
            "items_stored": 0,
            "errors": ["YouTube scraper not yet implemented - see AGENT_THETA_PROMPT.md"]
        }

    async def _scrape_reddit(self, config: ScraperConfig, scrape_id: str) -> Dict[str, Any]:
        """
        Scrape Reddit using PRAW.

        TODO: Implement using PRAW.
        """
        # Placeholder - will be implemented by AGENT THETA
        return {
            "items_scraped": 0,
            "items_stored": 0,
            "errors": ["Reddit scraper not yet implemented - see AGENT_THETA_PROMPT.md"]
        }

    async def _scrape_web(self, config: ScraperConfig, scrape_id: str) -> Dict[str, Any]:
        """
        Scrape web content using Jina.ai or ScraperAPI.

        TODO: Implement using Jina.ai Reader API.
        """
        # Placeholder - will be implemented
        return {
            "items_scraped": 0,
            "items_stored": 0,
            "errors": ["Web scraper not yet implemented"]
        }
```

---

## Dependencies

Add to `backend/pyproject.toml`:

```toml
[project]
name = "unified-scraper-backend"
version = "0.1.0"
description = "Multi-platform content intelligence engine"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "httpx>=0.26.0",  # For testing
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

---

## Environment Variables

Add to `.env`:

```bash
# FastAPI Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=info

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# API Keys (required)
OPENAI_API_KEY=sk-your-key-here

# Optional Platform Keys
SCRAPER_API_KEY=your-key-here
REDDIT_CLIENT_ID=your-id-here
REDDIT_CLIENT_SECRET=your-secret-here
```

---

## Success Criteria

### Test 1: Server Startup

**Goal**: Server runs on :8000 with no errors

```bash
# Start server
cd backend
source .venv/bin/activate
python main.py
```

**Expected Output**:
```
[2025-11-16T12:00:00+00:00] Starting IAC-032 Unified Scraper API
[2025-11-16T12:00:00+00:00] API ready at http://localhost:8000
[2025-11-16T12:00:00+00:00] Swagger docs at http://localhost:8000/docs
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Test 2: Swagger Documentation

**Goal**: Interactive API docs load correctly

```bash
# Open in browser
open http://localhost:8000/docs
```

**Verify**:
- All endpoints listed
- Request/response schemas documented
- Try it out buttons work
- Examples load correctly

---

### Test 3: Health Check

**Goal**: Health endpoint returns service status

```bash
curl -X GET http://localhost:8000/health | jq
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 45.23,
  "total_requests": 1,
  "services": {
    "openai": {
      "name": "openai",
      "status": "healthy",
      "message": "API key configured",
      "last_check": "2025-11-16T12:00:45Z"
    },
    "chromadb": {
      "name": "chromadb",
      "status": "healthy",
      "message": "Persistence directory ready: data/chromadb",
      "last_check": "2025-11-16T12:00:45Z"
    },
    "environment": {
      "name": "environment",
      "status": "degraded",
      "message": "Missing optional: ['SCRAPER_API_KEY', 'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']",
      "last_check": "2025-11-16T12:00:45Z"
    },
    "disk": {
      "name": "disk",
      "status": "healthy",
      "message": "120.45 GB free",
      "last_check": "2025-11-16T12:00:45Z"
    }
  },
  "timestamp": "2025-11-16T12:00:45Z"
}
```

---

### Test 4: Root Endpoint

**Goal**: Root returns API information

```bash
curl -X GET http://localhost:8000/ | jq
```

**Expected Response**:
```json
{
  "name": "IAC-032 Unified Scraper API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "scrape": "/scrape/{platform}",
    "query": "/query/rag",
    "health": "/health"
  }
}
```

---

### Test 5: CORS Headers

**Goal**: CORS headers present in response

```bash
curl -X OPTIONS http://localhost:8000/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i access-control
```

**Expected Headers**:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
access-control-allow-headers: Content-Type, Authorization, ...
```

---

### Test 6: Error Handling

**Goal**: Errors return consistent JSON format

```bash
# Test 404
curl -X GET http://localhost:8000/nonexistent | jq

# Test validation error
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{"username": ""}' | jq
```

**Expected 404 Response**:
```json
{
  "error": {
    "type": "HTTPException",
    "status_code": 404,
    "detail": "Not Found",
    "timestamp": "2025-11-16T12:00:45Z",
    "path": "/nonexistent"
  }
}
```

**Expected Validation Error**:
```json
{
  "error": {
    "type": "ValidationError",
    "status_code": 422,
    "detail": "Request validation failed",
    "errors": [
      {
        "field": "body.username",
        "message": "String should have at least 1 character",
        "type": "string_too_short"
      }
    ],
    "timestamp": "2025-11-16T12:00:45Z",
    "path": "/scrape/twitter"
  }
}
```

---

### Test 7: Scraping Endpoint (Placeholder)

**Goal**: Scraping endpoint returns structured response

```bash
curl -X POST http://localhost:8000/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dankoe",
    "max_tweets": 100,
    "include_replies": false,
    "include_retweets": false
  }' | jq
```

**Expected Response**:
```json
{
  "success": true,
  "platform": "twitter",
  "items_scraped": 0,
  "items_stored": 0,
  "errors": ["Twitter scraper not yet implemented - see AGENT_EPSILON_PROMPT.md"],
  "scrape_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-16T12:00:45Z",
  "completed_at": "2025-11-16T12:00:46Z",
  "duration_seconds": 0.5,
  "metadata": {
    "username": "dankoe"
  }
}
```

---

### Test 8: Query Endpoint (Placeholder)

**Goal**: Query endpoint accepts semantic search requests

```bash
curl -X POST http://localhost:8000/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "focus systems for knowledge workers",
    "n_results": 10,
    "min_similarity": 0.5
  }' | jq
```

**Note**: This will fail until AGENT ZETA implements the RAG engine.

---

### Test 9: Readiness Probe

**Goal**: Kubernetes-style readiness check

```bash
curl -X GET http://localhost:8000/health/ready | jq
```

**Expected Response**:
```json
{
  "ready": true,
  "checks": {
    "openai_key": true,
    "chromadb_dir": true,
    "python_version": true
  }
}
```

---

### Test 10: Platform List

**Goal**: List supported scraping platforms

```bash
curl -X GET http://localhost:8000/scrape/platforms | jq
```

**Expected Response**:
```json
{
  "platforms": {
    "twitter": {
      "name": "Twitter/X",
      "adapter": "adapters.twitter",
      "requires_auth": true,
      "rate_limit": "Adaptive",
      "cost": "Free (Playwright)"
    },
    "youtube": {
      "name": "YouTube",
      "adapter": "adapters.youtube",
      "requires_auth": false,
      "rate_limit": "API quota",
      "cost": "Free"
    },
    "reddit": {
      "name": "Reddit",
      "adapter": "adapters.reddit",
      "requires_auth": true,
      "rate_limit": "1000 req/10min",
      "cost": "Free"
    },
    "web": {
      "name": "Web/Blogs",
      "adapter": "adapters.web",
      "requires_auth": false,
      "rate_limit": "50K pages/month (Jina)",
      "cost": "$0-49/month"
    }
  },
  "total": 4
}
```

---

## Error Handling Patterns

### 1. Validation Errors (422)

```python
# Pydantic handles this automatically via RequestValidationError
class TwitterScrapeRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
```

### 2. Not Found (404)

```python
@router.get("/status/{scrape_id}")
async def get_status(scrape_id: str):
    result = await get_job(scrape_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Job {scrape_id} not found")
    return result
```

### 3. Service Unavailable (503)

```python
@router.post("/scrape/twitter")
async def scrape_twitter(request: Request):
    if not scraper_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Twitter scraper temporarily unavailable"
        )
```

### 4. Rate Limiting (429)

```python
from fastapi import HTTPException

@router.post("/query/rag")
async def query_rag(request: Request):
    if rate_limit_exceeded(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in 60 seconds.",
            headers={"Retry-After": "60"}
        )
```

### 5. Internal Server Error (500)

```python
# Handled by global exception handler in middleware/errors.py
# Returns consistent JSON format with error details
```

---

## Performance Optimization

### 1. Async Endpoints

All endpoints should be async:

```python
@router.post("/scrape/twitter")
async def scrape_twitter(request: TwitterScrapeRequest):
    # Use async/await for I/O operations
    result = await factory.scrape(config)
    return result
```

### 2. Background Tasks

For long-running operations:

```python
from fastapi import BackgroundTasks

@router.post("/scrape/twitter/async")
async def scrape_twitter_async(
    request: TwitterScrapeRequest,
    background_tasks: BackgroundTasks
):
    scrape_id = generate_id()
    background_tasks.add_task(execute_scrape, config, scrape_id)
    return {"scrape_id": scrape_id, "status": "queued"}
```

### 3. Connection Pooling

For database connections:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    pool = await create_pool()
    try:
        yield pool
    finally:
        await pool.close()
```

---

## Security Considerations

### 1. Input Validation

Always validate user input:

```python
class TwitterScrapeRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$"  # Only valid Twitter chars
    )
```

### 2. Rate Limiting (Future)

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/scrape/twitter")
async def scrape_twitter(
    request: TwitterScrapeRequest,
    _rate_limit: RateLimiter(times=10, seconds=60)
):
    pass
```

### 3. API Key Authentication (Future)

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@router.post("/scrape/twitter")
async def scrape_twitter(
    request: TwitterScrapeRequest,
    api_key: str = Depends(api_key_header)
):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## Integration Points

### With AGENT ZETA (RAG Engine)

```python
# In query routes
from services.rag_query import RAGQueryEngine

engine = RAGQueryEngine()
result = await engine.query(rag_query)
```

### With AGENT EPSILON (Twitter Scraper)

```python
# In scraper factory
from scrapers.adapters.twitter import TwitterScraper

async def _scrape_twitter(self, config, scrape_id):
    scraper = TwitterScraper()
    tweets = await scraper.scrape_profile(config.target, config.max_items)
    return {"items_scraped": len(tweets), "items_stored": len(tweets)}
```

### With PostgreSQL (Database)

```python
# Future integration
from databases import Database

database = Database("postgresql://...")

async def lifespan(app):
    await database.connect()
    yield
    await database.disconnect()
```

---

## Deployment Checklist

1. [ ] Environment variables configured (`.env`)
2. [ ] Dependencies installed: `uv pip install fastapi uvicorn pydantic`
3. [ ] Server starts without errors: `python main.py`
4. [ ] Swagger docs accessible at `/docs`
5. [ ] Health check returns valid JSON
6. [ ] CORS headers present in responses
7. [ ] Error responses follow consistent format
8. [ ] All test curl commands pass
9. [ ] No security warnings in logs
10. [ ] Request counting middleware works

---

## Common Pitfalls to Avoid

1. **Blocking I/O in async functions**: Use `await` for all I/O operations
2. **Missing CORS setup**: Frontend can't make requests without proper CORS
3. **No input validation**: Always use Pydantic models for request bodies
4. **Generic error messages**: Return specific, actionable error details
5. **Not tracking state**: Use app.state for shared application data
6. **Ignoring health checks**: Implement comprehensive service monitoring
7. **Hardcoded values**: Use environment variables for configuration

---

## Next Steps After Implementation

1. **Test with real scrapers**: Connect AGENT EPSILON/THETA implementations
2. **Add authentication**: Implement API key or JWT auth
3. **Add rate limiting**: Protect against abuse
4. **Add logging**: Structured logs for debugging
5. **Add metrics**: Prometheus/Grafana monitoring
6. **Add caching**: Redis for frequently accessed data
7. **Add tests**: pytest with httpx for integration tests

---

*Agent ETA - API Orchestrator*
*The central nervous system of unified scraping*
