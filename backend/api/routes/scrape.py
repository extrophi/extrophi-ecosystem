"""Scraping API endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.db.models import ScrapeJobModel, ScrapeJobORM
from backend.queue.redis_queue import get_queue

router = APIRouter(prefix="/scrape", tags=["scraping"])


class ScrapeRequest(BaseModel):
    target: str
    limit: int = 20


class ScrapeResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/{platform}", response_model=ScrapeResponse)
async def scrape_platform(
    platform: str, request: ScrapeRequest, db: Session = Depends(get_session)
):
    """
    Queue a scrape job for the specified platform.

    Args:
        platform: twitter, youtube, reddit, web
        request: target identifier and limit

    Returns:
        Job ID and status
    """
    valid_platforms = ["twitter", "youtube", "reddit", "web"]
    if platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {valid_platforms}",
        )

    try:
        # Create job in database
        job_id = uuid4()
        job = ScrapeJobORM(
            id=job_id, platform=platform, target=request.target, limit=request.limit
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Queue the job in Redis
        queue = get_queue()
        queued = queue.enqueue(str(job_id), platform, request.target, request.limit)

        if not queued:
            raise HTTPException(status_code=503, detail="Failed to queue job")

        # Set initial status in Redis
        queue.set_job_status(str(job_id), "pending")

        return ScrapeResponse(
            job_id=str(job_id),
            status="queued",
            message=f"Scrape job queued for {platform}: {request.target}",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ScrapeJobModel)
async def get_job_status(job_id: str, db: Session = Depends(get_session)):
    """
    Get the status of a scrape job.

    Args:
        job_id: UUID of the job

    Returns:
        Job status and details
    """
    try:
        # Get job from database
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Convert to Pydantic model
        return ScrapeJobModel.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
