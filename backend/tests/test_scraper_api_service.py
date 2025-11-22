"""Tests for ScraperAPI service."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.scraper_api_service import (
    ScraperAPIConfig,
    ScraperAPIRateLimitExceeded,
    ScraperAPIService,
)


@pytest.fixture
def scraper_config():
    """Create test configuration."""
    return ScraperAPIConfig(
        api_key="test_key_123",
        max_credits=100,
        max_retries=3,
        initial_backoff=0.1,  # Short backoff for testing
    )


@pytest.fixture
def scraper_service(scraper_config):
    """Create ScraperAPI service instance."""
    return ScraperAPIService(scraper_config)


class TestScraperAPIConfig:
    """Test ScraperAPIConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ScraperAPIConfig(api_key="test_key")

        assert config.api_key == "test_key"
        assert config.max_credits == 4800
        assert config.max_retries == 3
        assert config.initial_backoff == 1.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ScraperAPIConfig(
            api_key="custom_key",
            max_credits=1000,
            max_retries=5,
            initial_backoff=2.0,
        )

        assert config.api_key == "custom_key"
        assert config.max_credits == 1000
        assert config.max_retries == 5
        assert config.initial_backoff == 2.0


class TestScraperAPIService:
    """Test ScraperAPI service."""

    def test_service_initialization(self, scraper_service, scraper_config):
        """Test service initialization."""
        assert scraper_service.config == scraper_config
        assert scraper_service._credits_used == 0

    def test_estimate_credits_basic(self, scraper_service):
        """Test basic credit estimation."""
        credits = scraper_service._estimate_credits("http://example.com", {})
        assert credits == 1

    def test_estimate_credits_javascript(self, scraper_service):
        """Test credit estimation with JavaScript rendering."""
        credits = scraper_service._estimate_credits(
            "http://example.com", {"render": True}
        )
        assert credits == 5

    def test_estimate_credits_premium(self, scraper_service):
        """Test credit estimation with premium proxy."""
        credits = scraper_service._estimate_credits(
            "http://example.com", {"premium": True}
        )
        assert credits == 10

    def test_estimate_credits_residential(self, scraper_service):
        """Test credit estimation with residential proxy."""
        credits = scraper_service._estimate_credits(
            "http://example.com", {"country_code": "us"}
        )
        assert credits == 25

    @pytest.mark.asyncio
    async def test_check_credit_limit_within_limit(self, scraper_service):
        """Test credit limit check when within limit."""
        with patch.object(
            scraper_service, "_get_total_credits_used", return_value=50
        ):
            # Should not raise exception
            await scraper_service._check_credit_limit()

    @pytest.mark.asyncio
    async def test_check_credit_limit_exceeded(self, scraper_service):
        """Test credit limit check when limit exceeded."""
        with patch.object(
            scraper_service, "_get_total_credits_used", return_value=101
        ):
            with pytest.raises(ScraperAPIRateLimitExceeded):
                await scraper_service._check_credit_limit()

    @pytest.mark.asyncio
    async def test_get_remaining_credits(self, scraper_service):
        """Test getting remaining credits."""
        with patch.object(
            scraper_service, "_get_total_credits_used", return_value=30
        ):
            remaining = await scraper_service.get_remaining_credits()
            assert remaining == 70  # 100 - 30

    @pytest.mark.asyncio
    async def test_get_remaining_credits_zero(self, scraper_service):
        """Test getting remaining credits when all used."""
        with patch.object(
            scraper_service, "_get_total_credits_used", return_value=150
        ):
            remaining = await scraper_service.get_remaining_credits()
            assert remaining == 0  # Can't go negative

    @pytest.mark.asyncio
    async def test_get_stats(self, scraper_service):
        """Test getting usage statistics."""
        with patch.object(
            scraper_service, "_get_total_credits_used", return_value=60
        ):
            stats = await scraper_service.get_stats()

            assert stats["total_credits_used"] == 60
            assert stats["credits_limit"] == 100
            assert stats["credits_remaining"] == 40
            assert stats["percentage_used"] == 60.0

    @pytest.mark.asyncio
    async def test_scrape_success(self, scraper_service):
        """Test successful scrape."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.status_code = 200

        with patch.object(
            scraper_service.client, "get", return_value=mock_response
        ):
            with patch.object(
                scraper_service, "_check_credit_limit", return_value=None
            ):
                with patch.object(
                    scraper_service, "_log_usage", return_value=None
                ):
                    result = await scraper_service.scrape("http://example.com")

                    assert result["url"] == "http://example.com"
                    assert result["status_code"] == 200
                    assert result["credits_used"] == 1
                    assert "Test content" in result["content"]

    @pytest.mark.asyncio
    async def test_scrape_with_retry(self, scraper_service):
        """Test scrape with retry on failure."""
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_response.status_code = 200

        # Fail twice, then succeed
        with patch.object(
            scraper_service.client,
            "get",
            side_effect=[Exception("Network error"), Exception("Timeout"), mock_response],
        ):
            with patch.object(
                scraper_service, "_check_credit_limit", return_value=None
            ):
                with patch.object(
                    scraper_service, "_log_usage", return_value=None
                ):
                    result = await scraper_service.scrape("http://example.com")
                    assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_scrape_all_retries_failed(self, scraper_service):
        """Test scrape when all retries fail."""
        with patch.object(
            scraper_service.client,
            "get",
            side_effect=Exception("Network error"),
        ):
            with patch.object(
                scraper_service, "_check_credit_limit", return_value=None
            ):
                with patch.object(
                    scraper_service, "_log_usage", return_value=None
                ):
                    with pytest.raises(Exception, match="Failed to scrape"):
                        await scraper_service.scrape("http://example.com")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("SCRAPERAPI_KEY"),
    reason="SCRAPERAPI_KEY not set",
)
class TestScraperAPIIntegration:
    """Integration tests requiring real API key."""

    @pytest.mark.asyncio
    async def test_real_scrape(self):
        """Test real scrape with ScraperAPI."""
        config = ScraperAPIConfig(
            api_key=os.getenv("SCRAPERAPI_KEY"),
            max_credits=10,  # Low limit for testing
        )
        service = ScraperAPIService(config)

        # Mock database calls
        with patch.object(
            service, "_get_total_credits_used", return_value=0
        ):
            with patch.object(service, "_log_usage", return_value=None):
                result = await service.scrape("http://httpbin.org/html")

                assert result["status_code"] == 200
                assert len(result["content"]) > 0
                assert result["credits_used"] > 0
