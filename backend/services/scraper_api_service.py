"""ScraperAPI integration service with rate limiting and usage tracking."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from scraperapi_sdk import ScraperAPIClient
from sqlalchemy import text

from backend.db.connection import get_engine

logger = logging.getLogger(__name__)


@dataclass
class ScraperAPIConfig:
    """Configuration for ScraperAPI service."""

    api_key: str
    max_credits: int = 4800  # Stop if > 4,800 credits used
    max_retries: int = 3
    initial_backoff: float = 1.0  # Initial backoff in seconds


class ScraperAPIRateLimitExceeded(Exception):
    """Raised when ScraperAPI credit limit is exceeded."""

    pass


class ScraperAPIService:
    """
    ScraperAPI client wrapper with error handling, retry logic, and usage tracking.

    Features:
    - Automatic retry with exponential backoff
    - Credit usage tracking and limits
    - Database logging to scraper_usage table
    - Error handling for common failure modes
    """

    def __init__(self, config: ScraperAPIConfig):
        """
        Initialize ScraperAPI service.

        Args:
            config: ScraperAPI configuration
        """
        self.config = config
        self.client = ScraperAPIClient(api_key=config.api_key)
        self._credits_used = 0

    async def scrape(self, url: str, **kwargs) -> dict:
        """
        Scrape a URL using ScraperAPI with retry logic.

        Args:
            url: URL to scrape
            **kwargs: Additional parameters for ScraperAPI (render=True, country_code, etc.)

        Returns:
            Dictionary with scrape results:
            {
                "url": str,
                "content": str,
                "status_code": int,
                "credits_used": int,
                "scraped_at": str (ISO timestamp)
            }

        Raises:
            ScraperAPIRateLimitExceeded: If credit limit exceeded
            Exception: If scrape fails after all retries
        """
        # Check credit limit
        await self._check_credit_limit()

        # Track scrape start
        start_time = time.time()
        last_error = None

        # Retry loop with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"Scraping URL (attempt {attempt + 1}/{self.config.max_retries}): {url}"
                )

                # Make ScraperAPI request (synchronous)
                response = await asyncio.to_thread(
                    self.client.get, url=url, **kwargs
                )

                # Calculate credits used (estimate based on request type)
                credits_used = self._estimate_credits(url, kwargs)
                self._credits_used += credits_used

                # Build result
                result = {
                    "url": url,
                    "content": response.text if hasattr(response, 'text') else str(response),
                    "status_code": response.status_code if hasattr(response, 'status_code') else 200,
                    "credits_used": credits_used,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "elapsed_time": time.time() - start_time,
                }

                # Log successful scrape to database
                await self._log_usage(
                    url=url,
                    status="success",
                    credits_used=credits_used,
                    response_code=result["status_code"],
                    elapsed_time=result["elapsed_time"],
                )

                logger.info(
                    f"Successfully scraped {url} in {result['elapsed_time']:.2f}s "
                    f"(credits: {credits_used})"
                )

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Scrape attempt {attempt + 1} failed for {url}: {str(e)}"
                )

                # Don't retry on rate limit errors
                if "rate limit" in str(e).lower() or "429" in str(e):
                    await self._log_usage(
                        url=url,
                        status="failed",
                        credits_used=0,
                        error_message="Rate limit exceeded",
                    )
                    raise

                # Calculate backoff time with exponential increase
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.initial_backoff * (2 ** attempt)
                    logger.info(f"Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)

        # All retries failed
        elapsed_time = time.time() - start_time
        await self._log_usage(
            url=url,
            status="failed",
            credits_used=0,
            error_message=str(last_error),
            elapsed_time=elapsed_time,
        )

        raise Exception(
            f"Failed to scrape {url} after {self.config.max_retries} attempts: {last_error}"
        )

    async def _check_credit_limit(self) -> None:
        """
        Check if credit limit has been exceeded.

        Raises:
            ScraperAPIRateLimitExceeded: If credit limit exceeded
        """
        # Get total credits used from database
        total_credits = await self._get_total_credits_used()

        if total_credits >= self.config.max_credits:
            raise ScraperAPIRateLimitExceeded(
                f"ScraperAPI credit limit exceeded: {total_credits}/{self.config.max_credits} credits used"
            )

    def _estimate_credits(self, url: str, params: dict) -> int:
        """
        Estimate credits used for a ScraperAPI request.

        ScraperAPI pricing:
        - Basic request: 1 credit
        - JavaScript rendering: 5 credits
        - Premium proxy: 10 credits
        - Residential proxy: 25 credits

        Args:
            url: URL scraped
            params: Request parameters

        Returns:
            Estimated credits used
        """
        credits = 1  # Base cost

        # JavaScript rendering
        if params.get("render") or params.get("javascript"):
            credits = 5

        # Premium proxies
        if params.get("premium"):
            credits = 10

        # Residential proxies
        if params.get("country_code") or params.get("session_number"):
            credits = 25

        return credits

    async def _get_total_credits_used(self) -> int:
        """
        Get total credits used from database.

        Returns:
            Total credits used
        """
        try:
            engine = get_engine()

            query = text("""
                SELECT COALESCE(SUM(credits_used), 0) as total
                FROM scraper_usage
                WHERE scraper_type = 'scraperapi'
                AND status = 'success'
            """)

            with engine.connect() as conn:
                result = conn.execute(query).fetchone()
                return int(result[0]) if result else 0

        except Exception as e:
            logger.warning(f"Failed to get total credits from database: {e}")
            return self._credits_used  # Fallback to in-memory counter

    async def _log_usage(
        self,
        url: str,
        status: str,
        credits_used: int,
        response_code: Optional[int] = None,
        error_message: Optional[str] = None,
        elapsed_time: Optional[float] = None,
    ) -> None:
        """
        Log scraper usage to database.

        Args:
            url: URL scraped
            status: "success" or "failed"
            credits_used: Number of credits consumed
            response_code: HTTP response code
            error_message: Error message if failed
            elapsed_time: Time elapsed in seconds
        """
        try:
            engine = get_engine()

            query = text("""
                INSERT INTO scraper_usage (
                    scraper_type,
                    url,
                    status,
                    credits_used,
                    response_code,
                    error_message,
                    elapsed_time,
                    scraped_at
                ) VALUES (
                    :scraper_type,
                    :url,
                    :status,
                    :credits_used,
                    :response_code,
                    :error_message,
                    :elapsed_time,
                    :scraped_at
                )
            """)

            with engine.connect() as conn:
                conn.execute(
                    query,
                    {
                        "scraper_type": "scraperapi",
                        "url": url,
                        "status": status,
                        "credits_used": credits_used,
                        "response_code": response_code,
                        "error_message": error_message,
                        "elapsed_time": elapsed_time,
                        "scraped_at": datetime.utcnow(),
                    },
                )
                conn.commit()

            logger.debug(f"Logged usage for {url}: {status}, {credits_used} credits")

        except Exception as e:
            logger.error(f"Failed to log usage to database: {e}")

    async def get_remaining_credits(self) -> int:
        """
        Get remaining credits available.

        Returns:
            Number of credits remaining
        """
        total_used = await self._get_total_credits_used()
        return max(0, self.config.max_credits - total_used)

    async def get_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Statistics dictionary
        """
        total_used = await self._get_total_credits_used()

        return {
            "total_credits_used": total_used,
            "credits_limit": self.config.max_credits,
            "credits_remaining": max(0, self.config.max_credits - total_used),
            "percentage_used": (total_used / self.config.max_credits * 100)
            if self.config.max_credits > 0
            else 0,
        }


# Global ScraperAPI service instance
_GLOBAL_SCRAPER_SERVICE: Optional[ScraperAPIService] = None


def get_scraper_api_service(api_key: Optional[str] = None) -> ScraperAPIService:
    """
    Get global ScraperAPI service instance.

    Args:
        api_key: ScraperAPI key (required on first call)

    Returns:
        ScraperAPIService instance
    """
    global _GLOBAL_SCRAPER_SERVICE

    if _GLOBAL_SCRAPER_SERVICE is None:
        if api_key is None:
            raise ValueError("ScraperAPI key required on first initialization")

        config = ScraperAPIConfig(api_key=api_key)
        _GLOBAL_SCRAPER_SERVICE = ScraperAPIService(config)

    return _GLOBAL_SCRAPER_SERVICE
