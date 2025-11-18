"""
Research Module FastAPI Backend

Provides endpoints for card enrichment and content scraping.
Integrates with Writer module via CORS-enabled API.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from dotenv import load_dotenv

# Import database modules
from db import get_db_manager, ContentCRUD, SourceCRUD, ScrapeJobCRUD, VectorSearch

# Import enrichment engine
from enrichment import EnrichmentEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Research Module API",
    description="Content enrichment and scraping service for BrainDump v3.0",
    version="1.0.0",
)

# Global enrichment engine instance (initialized on startup)
enrichment_engine: Optional[EnrichmentEngine] = None

# Configure CORS for Writer module
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:1420",  # Tauri dev
        "tauri://localhost",      # Tauri production
        "https://tauri.localhost", # Tauri production alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================

class Source(BaseModel):
    """External content source metadata"""
    platform: str = Field(..., description="Platform name (twitter, youtube, reddit, web)")
    url: HttpUrl = Field(..., description="Source URL")
    title: Optional[str] = Field(None, description="Content title")
    author: Optional[str] = Field(None, description="Content author/creator")
    timestamp: Optional[datetime] = Field(None, description="Publication timestamp")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Semantic similarity score")


class Suggestion(BaseModel):
    """Content enrichment suggestion"""
    text: str = Field(..., description="Suggested text to add")
    type: str = Field(..., description="Suggestion type (fact, example, quote, statistic)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: Optional[Source] = Field(None, description="Source of suggestion")


class EnrichRequest(BaseModel):
    """Request model for card enrichment"""
    card_id: str = Field(..., description="Unique card identifier")
    content: str = Field(..., min_length=1, description="Card content to enrich")
    context: Optional[str] = Field(None, description="Additional context from surrounding cards")
    max_suggestions: int = Field(5, ge=1, le=20, description="Maximum number of suggestions to return")


class EnrichResponse(BaseModel):
    """Response model for card enrichment"""
    card_id: str = Field(..., description="Card identifier from request")
    suggestions: List[Suggestion] = Field(default_factory=list, description="Content suggestions")
    sources: List[Source] = Field(default_factory=list, description="Related sources")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ScrapeRequest(BaseModel):
    """Request model for content scraping"""
    url: HttpUrl = Field(..., description="URL to scrape")
    platform: Optional[str] = Field(None, description="Platform hint (twitter, youtube, reddit, web)")
    depth: int = Field(1, ge=1, le=3, description="Scraping depth (1=single page, 2=related links, 3=deep)")
    extract_embeddings: bool = Field(True, description="Generate embeddings for scraped content")


class ScrapeResponse(BaseModel):
    """Response model for scraping job"""
    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Job status (pending, processing, completed, failed)")
    url: HttpUrl = Field(..., description="URL being scraped")
    estimated_time_seconds: Optional[int] = Field(None, description="Estimated completion time")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns service status and component health information.
    """
    logger.info("Health check requested")

    # Check database health
    db_manager = get_db_manager()
    db_health = await db_manager.health_check()

    # Determine overall database status
    db_status = "healthy" if db_health.get("status") == "healthy" else "unhealthy"

    # Check enrichment engine health
    enrichment_status = "disabled"
    if enrichment_engine:
        try:
            engine_health = await enrichment_engine.health_check()
            enrichment_status = engine_health.get("overall", "unknown")
        except Exception as e:
            logger.error(f"Enrichment health check failed: {e}")
            enrichment_status = "unhealthy"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components={
            "api": "healthy",
            "database": db_status,
            "pgvector": "enabled" if db_health.get("pgvector_enabled") else "disabled",
            "enrichment_engine": enrichment_status,
            "embeddings": "healthy" if enrichment_engine else "disabled",
            "llm_analyzer": "healthy" if enrichment_engine else "disabled",
        }
    )


@app.post("/api/enrich", response_model=EnrichResponse, tags=["Enrichment"])
async def enrich_card(request: EnrichRequest):
    """
    Enrich card content with suggestions

    Accepts card content from Writer module and returns enrichment suggestions
    based on semantic search of scraped content database.

    Workflow:
    1. Generate embedding for content (LAMBDA)
    2. Vector similarity search (THETA)
    3. LLM analysis with GPT-4 (extract frameworks, patterns)
    4. Generate contextual suggestions
    5. Return suggestions with source attribution

    - **card_id**: Unique identifier for the card
    - **content**: Card text to enrich
    - **context**: Optional surrounding context
    - **max_suggestions**: Maximum suggestions to return (1-20)
    """
    logger.info(f"Enrichment requested for card_id={request.card_id}, content_length={len(request.content)}")

    if not enrichment_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enrichment engine not initialized. Check server logs."
        )

    start_time = datetime.utcnow()

    try:
        # Run enrichment pipeline
        result = await enrichment_engine.enrich(
            content=request.content,
            context=request.context,
            max_suggestions=request.max_suggestions,
            similarity_threshold=0.7,  # TODO: Make configurable via request
            enable_scraping=False  # Disabled for now (scrapers run async)
        )

        # Convert to API response format
        suggestions = []
        for sug in result['suggestions']:
            # Build source object if available
            source = None
            if sug.get('source'):
                source_data = sug['source']
                source = Source(
                    platform=source_data['platform'],
                    url=source_data['url'],
                    title=source_data.get('title'),
                    author=source_data.get('author'),
                    timestamp=None,  # Not always available
                    relevance_score=source_data.get('relevance_score')
                )

            suggestions.append(Suggestion(
                text=sug['text'],
                type=sug['type'],
                confidence=sug['confidence'],
                source=source
            ))

        # Convert sources to API format
        sources = []
        for src in result['sources']:
            sources.append(Source(
                platform=src['platform'],
                url=src['url'],
                title=src.get('title'),
                author=src.get('author'),
                timestamp=src.get('published_at'),
                relevance_score=src.get('relevance_score')
            ))

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(
            f"Enrichment completed for card_id={request.card_id}, "
            f"suggestions={len(suggestions)}, sources={len(sources)}, "
            f"time={processing_time:.2f}ms"
        )

        return EnrichResponse(
            card_id=request.card_id,
            suggestions=suggestions,
            sources=sources,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Enrichment failed for card_id={request.card_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}"
        )


@app.post("/api/scrape", response_model=ScrapeResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Scraping"])
async def trigger_scrape(request: ScrapeRequest):
    """
    Trigger content scraping job

    Initiates asynchronous scraping of specified URL. Supports multiple platforms:
    - Twitter/X profiles and threads
    - YouTube videos (transcript + metadata)
    - Reddit posts and threads
    - Generic web pages

    - **url**: URL to scrape
    - **platform**: Optional platform hint for specialized scraper
    - **depth**: Scraping depth (1=single page, 2=related, 3=deep)
    - **extract_embeddings**: Generate embeddings for semantic search
    """
    logger.info(f"Scrape requested for url={request.url}, platform={request.platform}, depth={request.depth}")

    # TODO: This is a skeleton implementation
    # Actual scraping logic will be implemented by IOTA agent
    # Job queue and status tracking will be added by MU agent

    import uuid
    job_id = str(uuid.uuid4())

    # Placeholder response
    logger.info(f"Scrape job created: job_id={job_id}, url={request.url}")

    return ScrapeResponse(
        job_id=job_id,
        status="pending",
        url=request.url,
        estimated_time_seconds=30,
        message=f"Scraping job queued. Platform: {request.platform or 'auto-detect'}, Depth: {request.depth}",
    )


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Returns basic API information and links to documentation.
    """
    return {
        "service": "Research Module API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "enrich": "POST /api/enrich",
            "scrape": "POST /api/scrape",
        }
    }


# ============================================================================
# Application Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    global enrichment_engine

    logger.info("Research Module API starting up...")
    logger.info("CORS enabled for Writer module")
    logger.info("Endpoints: /health, /api/enrich, /api/scrape")

    # Initialize database connection
    try:
        db_manager = get_db_manager()
        await db_manager.connect(min_size=10, max_size=20)
        logger.info("Database connection pool initialized")

        # Verify database health
        health = await db_manager.health_check()
        if health["status"] == "healthy":
            logger.info(f"Database: {health['version']}")
            logger.info(f"pgvector: {'enabled' if health['pgvector_enabled'] else 'disabled'}")
            logger.info(f"Pool: {health['pool_size']} connections ({health['pool_idle']} idle)")
        else:
            logger.error(f"Database health check failed: {health.get('error')}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("API will start but database operations will fail")

    # Initialize enrichment engine
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found - enrichment engine disabled")
            logger.warning("Set OPENAI_API_KEY environment variable to enable enrichment")
        else:
            logger.info("Initializing enrichment engine...")

            db_manager = get_db_manager()

            enrichment_engine = EnrichmentEngine(
                db_manager=db_manager,
                openai_api_key=openai_api_key,
                embedding_model="text-embedding-ada-002",
                llm_model=os.getenv("LLM_MODEL", "gpt-4")
            )

            await enrichment_engine.initialize()

            logger.info("✓ Enrichment engine initialized successfully")
            logger.info(f"  - Embedding model: text-embedding-ada-002")
            logger.info(f"  - LLM model: {os.getenv('LLM_MODEL', 'gpt-4')}")
            logger.info("  - Components: LAMBDA (embeddings) + THETA (vector search) + GPT-4 (analysis)")

    except Exception as e:
        logger.error(f"Failed to initialize enrichment engine: {e}", exc_info=True)
        logger.warning("Enrichment endpoints will return 503 errors")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Research Module API shutting down...")

    # Close database connection
    try:
        db_manager = get_db_manager()
        await db_manager.disconnect()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
