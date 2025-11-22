"""Ultra Learning API Routes

API endpoints for parsing content into ultra learning format.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.db.models import UltraLearningModel, UltraLearningORM
from backend.services.ultra_learning_parser import UltraLearningParser

router = APIRouter(prefix="/ultra-learning", tags=["ultra-learning"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ParseRequest(BaseModel):
    """Request to parse content into ultra learning format"""

    limit: Optional[int] = Field(None, description="Maximum number of items to process (None for all)")
    batch_size: Optional[int] = Field(100, description="Number of items per batch")
    sleep_between_batches: Optional[float] = Field(1.0, description="Seconds to sleep between batches")


class ParseResponse(BaseModel):
    """Response from parsing operation"""

    message: str
    stats: Dict[str, Any]


class UltraLearningListResponse(BaseModel):
    """Response for listing ultra learning items"""

    items: List[UltraLearningModel]
    total: int
    page: int
    page_size: int


class SubjectStatsResponse(BaseModel):
    """Response for subject statistics"""

    subjects: List[Dict[str, Any]]
    total_subjects: int
    total_items: int


# ============================================================================
# Routes
# ============================================================================


@router.post("/parse", response_model=ParseResponse, status_code=202)
async def parse_content(
    request: ParseRequest = ParseRequest(),
    session: Session = Depends(get_session),
):
    """
    Parse scraped content into ultra learning format.

    This endpoint processes content from the `contents` table and extracts:
    - Meta subject (main topic)
    - Concepts (key ideas, frameworks)
    - Facts (statistics, data points)
    - Procedures (step-by-step instructions)

    **Model**: Claude Haiku 4 (claude-haiku-4-20250514)
    **Cost**: ~$0.00025 per item (~$1.25 for 5,000 items)

    The parsing is done in batches with rate limiting to avoid overwhelming the API.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/ultra-learning/parse" \\
      -H "Content-Type: application/json" \\
      -d '{"limit": 100, "batch_size": 10, "sleep_between_batches": 1.0}'
    ```

    Args:
        request: Parse configuration (limit, batch_size, sleep_between_batches)
        session: Database session

    Returns:
        ParseResponse with processing statistics
    """
    try:
        # Initialize parser
        parser = UltraLearningParser(
            batch_size=request.batch_size or 100,
            sleep_between_batches=request.sleep_between_batches or 1.0,
        )

        # Process batch
        result = parser.process_batch(session, limit=request.limit)

        # Print report
        print(parser.get_report())

        return ParseResponse(message=result["message"], stats=result["stats"])

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse content: {str(e)}")


@router.get("", response_model=UltraLearningListResponse)
async def list_ultra_learning(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    meta_subject: Optional[str] = Query(None, description="Filter by meta subject (partial match)"),
    session: Session = Depends(get_session),
):
    """
    List ultra learning items with pagination and filtering.

    **Example**:
    ```bash
    # Get first page of YouTube content
    curl "http://localhost:8000/api/ultra-learning?platform=youtube&page=1&page_size=20"

    # Search by subject
    curl "http://localhost:8000/api/ultra-learning?meta_subject=marketing"
    ```

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        platform: Filter by platform (twitter, youtube, reddit, etc.)
        author_id: Filter by author ID
        meta_subject: Filter by meta subject (partial match)
        session: Database session

    Returns:
        Paginated list of ultra learning items
    """
    try:
        # Build query
        query = select(UltraLearningORM)

        # Apply filters
        if platform:
            query = query.where(UltraLearningORM.platform == platform)
        if author_id:
            query = query.where(UltraLearningORM.author_id == author_id)
        if meta_subject:
            query = query.where(UltraLearningORM.meta_subject.ilike(f"%{meta_subject}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = session.execute(count_query).scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(UltraLearningORM.created_at.desc()).offset(offset).limit(page_size)

        # Execute query
        items = session.execute(query).scalars().all()

        # Convert to Pydantic models
        item_models = [UltraLearningModel.model_validate(item) for item in items]

        return UltraLearningListResponse(items=item_models, total=total, page=page, page_size=page_size)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list ultra learning items: {str(e)}")


@router.get("/{content_id}", response_model=UltraLearningModel)
async def get_ultra_learning(
    content_id: str,
    session: Session = Depends(get_session),
):
    """
    Get ultra learning data for a specific content item.

    **Example**:
    ```bash
    curl "http://localhost:8000/api/ultra-learning/123e4567-e89b-12d3-a456-426614174000"
    ```

    Args:
        content_id: Content UUID
        session: Database session

    Returns:
        Ultra learning data for the content
    """
    try:
        # Query by content_id
        query = select(UltraLearningORM).where(UltraLearningORM.content_id == content_id)
        item = session.execute(query).scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail=f"Ultra learning data not found for content {content_id}")

        return UltraLearningModel.model_validate(item)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ultra learning data: {str(e)}")


@router.get("/subjects/stats", response_model=SubjectStatsResponse)
async def get_subject_stats(
    limit: int = Query(50, ge=1, le=500, description="Number of top subjects to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    session: Session = Depends(get_session),
):
    """
    Get statistics about meta subjects.

    Returns the top subjects by frequency, useful for understanding
    what topics are most common in the parsed content.

    **Example**:
    ```bash
    # Get top 10 subjects across all platforms
    curl "http://localhost:8000/api/ultra-learning/subjects/stats?limit=10"

    # Get top subjects for YouTube only
    curl "http://localhost:8000/api/ultra-learning/subjects/stats?platform=youtube"
    ```

    Args:
        limit: Number of top subjects to return
        platform: Filter by platform
        session: Database session

    Returns:
        Subject statistics with counts
    """
    try:
        # Build query
        query = select(UltraLearningORM.meta_subject, func.count(UltraLearningORM.id).label("count"))

        # Apply platform filter
        if platform:
            query = query.where(UltraLearningORM.platform == platform)

        # Group by subject and order by count
        query = query.group_by(UltraLearningORM.meta_subject).order_by(func.count(UltraLearningORM.id).desc()).limit(limit)

        # Execute query
        results = session.execute(query).all()

        # Format results
        subjects = [{"subject": row[0], "count": row[1]} for row in results]

        # Get total counts
        total_items_query = select(func.count(UltraLearningORM.id))
        if platform:
            total_items_query = total_items_query.where(UltraLearningORM.platform == platform)
        total_items = session.execute(total_items_query).scalar() or 0

        total_subjects_query = select(func.count(func.distinct(UltraLearningORM.meta_subject)))
        if platform:
            total_subjects_query = total_subjects_query.where(UltraLearningORM.platform == platform)
        total_subjects = session.execute(total_subjects_query).scalar() or 0

        return SubjectStatsResponse(subjects=subjects, total_subjects=total_subjects, total_items=total_items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subject stats: {str(e)}")


@router.get("/health", status_code=200)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ultra-learning"}
