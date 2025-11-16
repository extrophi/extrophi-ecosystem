"""Scraping API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.scrapers import get_scraper

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
    platform: str, request: ScrapeRequest, db: Session = Depends(get_session)
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
            detail=f"Invalid platform. Must be one of: {valid_platforms}",
        )

    try:
        scraper = get_scraper(platform)

        # Health check first
        health = await scraper.health_check()
        if health.get("status") != "ok":
            raise HTTPException(
                status_code=503,
                detail=f"Scraper not healthy: {health.get('message')}",
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
            content_ids=content_ids,
        )

    except HTTPException:
        raise
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
