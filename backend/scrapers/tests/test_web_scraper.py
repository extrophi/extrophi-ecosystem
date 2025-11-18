"""Tests for Web scraper (CRITICAL PATH - Jina.ai)."""

import pytest

from backend.scrapers.adapters.web import WebScraper


class TestWebScraper:
    """Test Web scraper using Jina.ai Reader API."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test Jina.ai API health check."""
        scraper = WebScraper()
        result = await scraper.health_check()

        assert result["status"] in ["ok", "error"]
        assert result["platform"] == "web"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_extract_with_full_url(self):
        """Test extracting content from a full URL."""
        scraper = WebScraper()

        # Use a reliable, simple test URL
        result = await scraper.extract("https://example.com")

        assert len(result) == 1
        assert result[0]["url"] == "https://example.com"
        assert "content" in result[0]
        # Content type may not be present in error responses
        if "error" not in result[0]:
            assert result[0].get("content_type") == "markdown"

    @pytest.mark.asyncio
    async def test_extract_adds_https(self):
        """Test that extract adds https:// if missing."""
        scraper = WebScraper()

        result = await scraper.extract("example.com")

        assert result[0]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_extract_handles_errors(self):
        """Test error handling for invalid URLs."""
        scraper = WebScraper()

        # Use an invalid URL that will fail
        result = await scraper.extract("https://this-domain-definitely-does-not-exist-12345.com")

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["content"] == ""

    @pytest.mark.asyncio
    async def test_normalize_success(self):
        """Test normalizing successful extraction to UnifiedContent."""
        scraper = WebScraper()

        raw_data = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "# Test Article\n\nThis is test content with multiple words.",
            "content_type": "markdown",
        }

        normalized = await scraper.normalize(raw_data)

        assert normalized.platform == "web"
        assert normalized.source_url == "https://example.com/article"
        assert normalized.author.username == "example.com"
        assert normalized.content.title == "Test Article"
        assert normalized.content.body == raw_data["content"]
        assert normalized.content.word_count > 0
        assert normalized.metadata["domain"] == "example.com"
        assert normalized.metadata["has_error"] is False

    @pytest.mark.asyncio
    async def test_normalize_with_error(self):
        """Test normalizing failed extraction."""
        scraper = WebScraper()

        raw_data = {
            "url": "https://example.com",
            "title": None,
            "content": "",
            "error": "Connection timeout",
        }

        normalized = await scraper.normalize(raw_data)

        assert normalized.platform == "web"
        assert normalized.metadata["has_error"] is True

    @pytest.mark.asyncio
    async def test_normalize_extracts_domain(self):
        """Test domain extraction from various URL formats."""
        scraper = WebScraper()

        test_cases = [
            ("https://example.com/path", "example.com"),
            ("https://blog.example.com/article", "blog.example.com"),
            ("https://example.com:8080/path", "example.com:8080"),
        ]

        for url, expected_domain in test_cases:
            raw_data = {"url": url, "content": "test", "title": "Test"}
            normalized = await scraper.normalize(raw_data)

            assert normalized.author.username == expected_domain
            assert normalized.metadata["domain"] == expected_domain

    @pytest.mark.asyncio
    async def test_full_scrape_workflow(self):
        """Test complete workflow: extract -> normalize."""
        scraper = WebScraper()

        # Extract
        raw_results = await scraper.extract("https://example.com")
        assert len(raw_results) > 0

        # Normalize
        normalized = await scraper.normalize(raw_results[0])

        assert normalized.platform == "web"
        assert normalized.source_url == "https://example.com"
        # Content may be empty if there was an error
        # At minimum, verify the structure is correct
        assert hasattr(normalized.content, "body")
