"""
Scraper Health Monitoring System

Tracks success rates, errors, uptime, and performance metrics for all scrapers.
Provides alerting when scrapers fail or performance degrades.

Author: PSI-2 Agent
Issue: #83 - Scraper health monitoring
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID

from db.connection import DatabaseManager

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Overall health status for a scraper"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    WARNING = "warning"
    CRITICAL = "critical"


class ErrorType(str, Enum):
    """Types of scraper errors"""
    HTTP_ERROR = "http_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class ScraperHealthMonitor:
    """
    Monitor and track scraper health metrics.

    Features:
    - Success rate tracking per platform
    - Error tracking with categorization
    - Uptime monitoring
    - Response time tracking
    - Alert triggering on failures

    Usage:
        monitor = ScraperHealthMonitor(db_manager)
        await monitor.record_success("twitter", items_scraped=10, response_time_ms=250)
        await monitor.record_failure("youtube", ErrorType.RATE_LIMIT, "Rate limit exceeded")
        health = await monitor.get_platform_health("twitter")
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize health monitor.

        Args:
            db_manager: Database connection manager
        """
        self.db = db_manager
        self.alert_thresholds = {
            "consecutive_failures": 3,  # Alert after 3 consecutive failures
            "success_rate_warning": 80.0,  # Warning if success rate < 80%
            "success_rate_critical": 50.0,  # Critical if success rate < 50%
        }

    async def record_success(
        self,
        platform: str,
        items_scraped: int = 0,
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record a successful scraper attempt.

        Args:
            platform: Platform name (twitter, youtube, reddit, web)
            items_scraped: Number of items successfully scraped
            response_time_ms: Response time in milliseconds
            metadata: Additional context

        Returns:
            UUID of created health metric record
        """
        logger.info(
            f"Recording success for {platform}: {items_scraped} items, "
            f"{response_time_ms}ms response time"
        )

        metric_id = await self.db.fetchval(
            """
            SELECT record_scraper_attempt($1, $2, NULL, NULL, NULL, $3, $4, $5)
            """,
            platform,
            "success",
            response_time_ms,
            items_scraped,
            metadata or {}
        )

        return metric_id

    async def record_failure(
        self,
        platform: str,
        error_type: ErrorType,
        error_message: str,
        http_status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record a failed scraper attempt.

        Args:
            platform: Platform name
            error_type: Type of error that occurred
            error_message: Human-readable error message
            http_status_code: HTTP status code if applicable
            response_time_ms: Response time before failure
            metadata: Additional context

        Returns:
            UUID of created health metric record
        """
        logger.warning(
            f"Recording failure for {platform}: {error_type.value} - {error_message}"
        )

        # Determine status based on error type
        status = "rate_limited" if error_type == ErrorType.RATE_LIMIT else "error"

        metric_id = await self.db.fetchval(
            """
            SELECT record_scraper_attempt($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            platform,
            status,
            error_type.value,
            error_message,
            http_status_code,
            response_time_ms,
            0,  # items_scraped
            metadata or {}
        )

        # Check if alert should be triggered
        await self._check_alerts(platform)

        return metric_id

    async def record_timeout(
        self,
        platform: str,
        timeout_seconds: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record a scraper timeout.

        Args:
            platform: Platform name
            timeout_seconds: Timeout duration in seconds
            metadata: Additional context

        Returns:
            UUID of created health metric record
        """
        return await self.record_failure(
            platform=platform,
            error_type=ErrorType.TIMEOUT,
            error_message=f"Request timed out after {timeout_seconds} seconds",
            response_time_ms=timeout_seconds * 1000,
            metadata=metadata
        )

    async def get_platform_health(
        self,
        platform: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive health status for a platform.

        Args:
            platform: Platform name
            time_window_hours: Time window for metrics calculation (default 24 hours)

        Returns:
            Dictionary containing:
            - status: HealthStatus enum
            - success_rate: Percentage of successful attempts
            - total_attempts: Total scraping attempts
            - successful_attempts: Number of successful attempts
            - failed_attempts: Number of failed attempts
            - avg_response_time_ms: Average response time
            - last_success_at: Timestamp of last successful scrape
            - last_failure_at: Timestamp of last failed scrape
            - consecutive_failures: Number of consecutive failures
            - uptime_percentage: Overall uptime percentage
        """
        # Get success rate statistics
        stats = await self.db.fetchrow(
            """
            SELECT * FROM get_success_rate_by_platform($1, $2)
            """,
            platform,
            time_window_hours
        )

        # Get uptime information
        uptime = await self.db.fetchrow(
            """
            SELECT * FROM scraper_uptime WHERE platform = $1
            """,
            platform
        )

        if not uptime:
            logger.warning(f"No uptime data found for platform: {platform}")
            return {
                "platform": platform,
                "status": HealthStatus.CRITICAL,
                "error": "Platform not initialized"
            }

        # Determine health status
        success_rate = float(stats["success_rate"]) if stats and stats["success_rate"] else 0.0
        consecutive_failures = uptime["consecutive_failures"]

        if consecutive_failures >= 5:
            status = HealthStatus.CRITICAL
        elif consecutive_failures >= 3:
            status = HealthStatus.WARNING
        elif success_rate < self.alert_thresholds["success_rate_critical"]:
            status = HealthStatus.CRITICAL
        elif success_rate < self.alert_thresholds["success_rate_warning"]:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return {
            "platform": platform,
            "status": status,
            "success_rate": success_rate,
            "total_attempts": int(stats["total_attempts"]) if stats else 0,
            "successful_attempts": int(stats["successful_attempts"]) if stats else 0,
            "failed_attempts": int(stats["failed_attempts"]) if stats else 0,
            "avg_response_time_ms": float(stats["avg_response_time_ms"]) if stats and stats["avg_response_time_ms"] else None,
            "last_success_at": uptime["last_success_at"],
            "last_failure_at": uptime["last_failure_at"],
            "consecutive_failures": consecutive_failures,
            "uptime_percentage": float(uptime["uptime_percentage"]),
            "time_window_hours": time_window_hours
        }

    async def get_all_platforms_health(
        self,
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get health status for all platforms.

        Args:
            time_window_hours: Time window for metrics calculation

        Returns:
            List of health status dictionaries for each platform
        """
        platforms = ["twitter", "youtube", "reddit", "web"]
        health_data = []

        for platform in platforms:
            health = await self.get_platform_health(platform, time_window_hours)
            health_data.append(health)

        return health_data

    async def get_error_breakdown(
        self,
        platform: str,
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get breakdown of errors by type for a platform.

        Args:
            platform: Platform name
            time_window_hours: Time window for error analysis

        Returns:
            List of error statistics by type
        """
        rows = await self.db.fetch(
            """
            SELECT * FROM get_error_breakdown_by_platform($1, $2)
            """,
            platform,
            time_window_hours
        )

        return [
            {
                "error_type": row["error_type"],
                "error_count": int(row["error_count"]),
                "percentage": float(row["percentage"]),
                "latest_occurrence": row["latest_occurrence"]
            }
            for row in rows
        ]

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary for all platforms.

        Returns:
            Dashboard data including:
            - overall_status: Worst status across all platforms
            - platforms: Health data for each platform
            - total_attempts_24h: Total scraping attempts in last 24 hours
            - total_successes_24h: Total successful scrapes
            - total_failures_24h: Total failed scrapes
            - avg_success_rate: Average success rate across platforms
        """
        rows = await self.db.fetch(
            """
            SELECT * FROM get_health_dashboard()
            """
        )

        platforms_health = []
        total_attempts = 0
        total_successes = 0
        total_failures = 0
        worst_status = HealthStatus.HEALTHY

        for row in rows:
            status = HealthStatus(row["status"])

            # Track worst status
            if status == HealthStatus.CRITICAL:
                worst_status = HealthStatus.CRITICAL
            elif status == HealthStatus.WARNING and worst_status != HealthStatus.CRITICAL:
                worst_status = HealthStatus.WARNING
            elif status == HealthStatus.DEGRADED and worst_status == HealthStatus.HEALTHY:
                worst_status = HealthStatus.DEGRADED

            platform_data = {
                "platform": row["platform"],
                "status": status,
                "success_rate": float(row["success_rate"]) if row["success_rate"] else 0.0,
                "last_success_at": row["last_success_at"],
                "last_failure_at": row["last_failure_at"],
                "consecutive_failures": row["consecutive_failures"],
                "uptime_percentage": float(row["uptime_percentage"]),
                "avg_response_time_ms": float(row["avg_response_time_ms"]) if row["avg_response_time_ms"] else None
            }
            platforms_health.append(platform_data)

        # Get 24-hour statistics
        stats = await self.db.fetch(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'success') as successes,
                COUNT(*) FILTER (WHERE status != 'success') as failures
            FROM scraper_health_metrics
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """
        )

        if stats:
            total_attempts = int(stats[0]["total"])
            total_successes = int(stats[0]["successes"])
            total_failures = int(stats[0]["failures"])

        avg_success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0.0

        return {
            "overall_status": worst_status,
            "platforms": platforms_health,
            "total_attempts_24h": total_attempts,
            "total_successes_24h": total_successes,
            "total_failures_24h": total_failures,
            "avg_success_rate": avg_success_rate,
            "timestamp": datetime.utcnow()
        }

    async def get_uptime_stats(
        self,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get uptime statistics.

        Args:
            platform: Optional platform name (if None, returns all platforms)

        Returns:
            Uptime statistics including last success/failure times and percentages
        """
        if platform:
            row = await self.db.fetchrow(
                """
                SELECT * FROM scraper_uptime WHERE platform = $1
                """,
                platform
            )

            if not row:
                raise ValueError(f"Platform not found: {platform}")

            return dict(row)
        else:
            rows = await self.db.fetch(
                """
                SELECT * FROM scraper_uptime ORDER BY platform
                """
            )

            return {
                "platforms": [dict(row) for row in rows]
            }

    async def _check_alerts(self, platform: str) -> None:
        """
        Check if alerts should be triggered for a platform.

        Args:
            platform: Platform name
        """
        uptime = await self.db.fetchrow(
            """
            SELECT consecutive_failures, uptime_percentage
            FROM scraper_uptime
            WHERE platform = $1
            """,
            platform
        )

        if not uptime:
            return

        consecutive_failures = uptime["consecutive_failures"]
        uptime_percentage = float(uptime["uptime_percentage"])

        # Alert on consecutive failures
        if consecutive_failures >= self.alert_thresholds["consecutive_failures"]:
            logger.error(
                f"🚨 ALERT: {platform} scraper has {consecutive_failures} consecutive failures!"
            )

        # Alert on low uptime
        if uptime_percentage < self.alert_thresholds["success_rate_critical"]:
            logger.error(
                f"🚨 ALERT: {platform} scraper uptime critically low: {uptime_percentage:.1f}%"
            )
        elif uptime_percentage < self.alert_thresholds["success_rate_warning"]:
            logger.warning(
                f"⚠️  WARNING: {platform} scraper uptime degraded: {uptime_percentage:.1f}%"
            )

    async def reset_platform_stats(self, platform: str) -> bool:
        """
        Reset statistics for a platform (admin use only).

        Args:
            platform: Platform name

        Returns:
            True if reset successful
        """
        logger.warning(f"Resetting health stats for platform: {platform}")

        await self.db.execute(
            """
            UPDATE scraper_uptime
            SET
                total_attempts = 0,
                total_successes = 0,
                total_failures = 0,
                consecutive_failures = 0,
                uptime_percentage = 100.0,
                last_success_at = NULL,
                last_failure_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE platform = $1
            """,
            platform
        )

        return True

    async def get_recent_metrics(
        self,
        platform: Optional[str] = None,
        limit: int = 100,
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent health metrics.

        Args:
            platform: Optional platform filter
            limit: Maximum number of records to return
            time_window_hours: Time window for metrics

        Returns:
            List of recent health metric records
        """
        if platform:
            query = """
                SELECT *
                FROM scraper_health_metrics
                WHERE platform = $1
                    AND timestamp > CURRENT_TIMESTAMP - ($2 || ' hours')::INTERVAL
                ORDER BY timestamp DESC
                LIMIT $3
            """
            rows = await self.db.fetch(query, platform, time_window_hours, limit)
        else:
            query = """
                SELECT *
                FROM scraper_health_metrics
                WHERE timestamp > CURRENT_TIMESTAMP - ($1 || ' hours')::INTERVAL
                ORDER BY timestamp DESC
                LIMIT $2
            """
            rows = await self.db.fetch(query, time_window_hours, limit)

        return [dict(row) for row in rows]
