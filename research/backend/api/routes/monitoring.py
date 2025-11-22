"""
Monitoring API Routes

Provides endpoints for scraper health monitoring, metrics, and dashboard data.

Author: PSI-2 Agent
Issue: #83 - Scraper health monitoring
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from db import get_db_manager
from monitoring import ScraperHealthMonitor, HealthStatus

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


# ============================================================================
# Response Models
# ============================================================================

class PlatformHealthResponse(BaseModel):
    """Health status for a single platform"""
    platform: str = Field(..., description="Platform name")
    status: HealthStatus = Field(..., description="Health status")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="Success rate percentage")
    total_attempts: int = Field(..., ge=0, description="Total scraping attempts")
    successful_attempts: int = Field(..., ge=0, description="Successful attempts")
    failed_attempts: int = Field(..., ge=0, description="Failed attempts")
    avg_response_time_ms: Optional[float] = Field(None, description="Average response time in ms")
    last_success_at: Optional[datetime] = Field(None, description="Last successful scrape timestamp")
    last_failure_at: Optional[datetime] = Field(None, description="Last failed scrape timestamp")
    consecutive_failures: int = Field(..., ge=0, description="Number of consecutive failures")
    uptime_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall uptime percentage")
    time_window_hours: int = Field(..., description="Time window for metrics calculation")


class ErrorBreakdownResponse(BaseModel):
    """Error statistics by type"""
    error_type: str = Field(..., description="Error type")
    error_count: int = Field(..., ge=0, description="Number of occurrences")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total errors")
    latest_occurrence: datetime = Field(..., description="Timestamp of latest occurrence")


class DashboardSummaryResponse(BaseModel):
    """Complete dashboard summary"""
    overall_status: HealthStatus = Field(..., description="Worst status across all platforms")
    platforms: List[Dict[str, Any]] = Field(..., description="Health data for each platform")
    total_attempts_24h: int = Field(..., ge=0, description="Total attempts in last 24 hours")
    total_successes_24h: int = Field(..., ge=0, description="Total successes in last 24 hours")
    total_failures_24h: int = Field(..., ge=0, description="Total failures in last 24 hours")
    avg_success_rate: float = Field(..., ge=0.0, le=100.0, description="Average success rate")
    timestamp: datetime = Field(..., description="Response timestamp")


class UptimeStatsResponse(BaseModel):
    """Uptime statistics"""
    platform: str = Field(..., description="Platform name")
    last_success_at: Optional[datetime] = Field(None, description="Last successful scrape")
    last_failure_at: Optional[datetime] = Field(None, description="Last failed scrape")
    consecutive_failures: int = Field(..., ge=0, description="Consecutive failures")
    total_attempts: int = Field(..., ge=0, description="Total attempts all-time")
    total_successes: int = Field(..., ge=0, description="Total successes all-time")
    total_failures: int = Field(..., ge=0, description="Total failures all-time")
    uptime_percentage: float = Field(..., ge=0.0, le=100.0, description="Uptime percentage")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")


class HealthMetricResponse(BaseModel):
    """Individual health metric record"""
    id: str = Field(..., description="Metric UUID")
    platform: str = Field(..., description="Platform name")
    status: str = Field(..., description="Status (success, error, rate_limited, timeout)")
    error_type: Optional[str] = Field(None, description="Error type if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    http_status_code: Optional[int] = Field(None, description="HTTP status code if applicable")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    items_scraped: int = Field(..., ge=0, description="Number of items scraped")
    timestamp: datetime = Field(..., description="Timestamp of attempt")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/health/{platform}", response_model=PlatformHealthResponse)
async def get_platform_health(
    platform: str,
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)")
):
    """
    Get health status for a specific platform.

    Returns comprehensive health metrics including:
    - Success rate and failure counts
    - Average response time
    - Last success/failure timestamps
    - Consecutive failure count
    - Overall uptime percentage

    **Supported platforms**: twitter, youtube, reddit, web
    """
    logger.info(f"Health check requested for platform: {platform}, window: {time_window_hours}h")

    if platform not in ["twitter", "youtube", "reddit", "web"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: twitter, youtube, reddit, web"
        )

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        health = await monitor.get_platform_health(platform, time_window_hours)

        return PlatformHealthResponse(**health)

    except Exception as e:
        logger.error(f"Error fetching health for {platform}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch health status: {str(e)}"
        )


@router.get("/health", response_model=List[PlatformHealthResponse])
async def get_all_platforms_health(
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)")
):
    """
    Get health status for all platforms.

    Returns health metrics for twitter, youtube, reddit, and web scrapers.
    """
    logger.info(f"Health check requested for all platforms, window: {time_window_hours}h")

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        health_data = await monitor.get_all_platforms_health(time_window_hours)

        return [PlatformHealthResponse(**h) for h in health_data]

    except Exception as e:
        logger.error(f"Error fetching health for all platforms: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch health status: {str(e)}"
        )


@router.get("/errors/{platform}", response_model=List[ErrorBreakdownResponse])
async def get_error_breakdown(
    platform: str,
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)")
):
    """
    Get breakdown of errors by type for a platform.

    Returns statistics for different error types:
    - HTTP errors
    - Rate limits
    - Timeouts
    - Parse errors
    - Authentication errors
    """
    logger.info(f"Error breakdown requested for {platform}, window: {time_window_hours}h")

    if platform not in ["twitter", "youtube", "reddit", "web"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: twitter, youtube, reddit, web"
        )

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        errors = await monitor.get_error_breakdown(platform, time_window_hours)

        return [ErrorBreakdownResponse(**e) for e in errors]

    except Exception as e:
        logger.error(f"Error fetching error breakdown for {platform}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch error breakdown: {str(e)}"
        )


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary():
    """
    Get comprehensive dashboard summary for all platforms.

    Returns:
    - Overall health status (worst status across all platforms)
    - Health data for each platform
    - 24-hour statistics (attempts, successes, failures)
    - Average success rate

    **Use this endpoint for main monitoring dashboard.**
    """
    logger.info("Dashboard summary requested")

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        summary = await monitor.get_dashboard_summary()

        return DashboardSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard summary: {str(e)}"
        )


@router.get("/uptime/{platform}", response_model=UptimeStatsResponse)
async def get_platform_uptime(platform: str):
    """
    Get uptime statistics for a specific platform.

    Returns all-time uptime data including:
    - Last success/failure timestamps
    - Consecutive failures
    - Total attempts/successes/failures
    - Uptime percentage
    """
    logger.info(f"Uptime stats requested for platform: {platform}")

    if platform not in ["twitter", "youtube", "reddit", "web"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: twitter, youtube, reddit, web"
        )

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        uptime = await monitor.get_uptime_stats(platform)

        return UptimeStatsResponse(**uptime)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching uptime for {platform}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch uptime stats: {str(e)}"
        )


@router.get("/uptime", response_model=Dict[str, List[UptimeStatsResponse]])
async def get_all_platforms_uptime():
    """
    Get uptime statistics for all platforms.

    Returns all-time uptime data for twitter, youtube, reddit, and web.
    """
    logger.info("Uptime stats requested for all platforms")

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        uptime_data = await monitor.get_uptime_stats()

        return {
            "platforms": [UptimeStatsResponse(**u) for u in uptime_data["platforms"]]
        }

    except Exception as e:
        logger.error(f"Error fetching uptime for all platforms: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch uptime stats: {str(e)}"
        )


@router.get("/metrics", response_model=List[HealthMetricResponse])
async def get_recent_metrics(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours")
):
    """
    Get recent health metrics.

    Returns individual scrape attempt records with detailed information.
    Useful for debugging and detailed analysis.

    **Query parameters:**
    - platform: Filter by specific platform (optional)
    - limit: Maximum number of records (1-1000)
    - time_window_hours: Time window for records (1-168 hours)
    """
    logger.info(
        f"Recent metrics requested: platform={platform}, limit={limit}, "
        f"window={time_window_hours}h"
    )

    if platform and platform not in ["twitter", "youtube", "reddit", "web"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: twitter, youtube, reddit, web"
        )

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        metrics = await monitor.get_recent_metrics(platform, limit, time_window_hours)

        return [HealthMetricResponse(**m) for m in metrics]

    except Exception as e:
        logger.error(f"Error fetching recent metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@router.post("/reset/{platform}", status_code=status.HTTP_200_OK)
async def reset_platform_stats(platform: str):
    """
    Reset statistics for a platform (admin use only).

    **WARNING**: This will clear all health statistics for the platform.
    Use with caution!
    """
    logger.warning(f"Reset requested for platform: {platform}")

    if platform not in ["twitter", "youtube", "reddit", "web"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: twitter, youtube, reddit, web"
        )

    try:
        db_manager = get_db_manager()
        monitor = ScraperHealthMonitor(db_manager)

        success = await monitor.reset_platform_stats(platform)

        return {
            "message": f"Statistics reset for {platform}",
            "platform": platform,
            "success": success,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error resetting stats for {platform}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset stats: {str(e)}"
        )
