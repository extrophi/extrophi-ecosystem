"""Web/Blog scraper using Jina.ai Reader API implementing BaseScraper interface."""
import os
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class WebScraper(BaseScraper):
    """
    Web scraper using Jina.ai Reader API.

    Features:
    - Free tier: 50,000 pages/month
    - Automatic markdown conversion
    - Clean content extraction
    - No JavaScript rendering needed for static sites
    """

    def __init__(self) -> None:
        self.jina_base_url = "https://r.jina.ai/"
        self.timeout = 30

    async def health_check(self) -> dict:
        """Verify Jina.ai API access."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.jina_base_url}https://example.com", timeout=10
                )
                if response.status_code == 200:
                    return {
                        "status": "ok",
                        "message": "Jina.ai Reader API accessible",
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "web",
                    }
        except Exception as e:
            pass

        return {
            "status": "error",
            "message": "Jina.ai Reader API not accessible",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "web",
        }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract content from web URL.

        Args:
            target: Full URL to scrape
            limit: Not used for single page extraction

        Returns:
            Raw web content as list of dicts
        """
        if not target.startswith("http"):
            target = f"https://{target}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.jina_base_url}{target}",
                    timeout=self.timeout,
                    headers={
                        "Accept": "text/markdown",
                        "X-Return-Format": "markdown",
                    },
                )
                response.raise_for_status()

                content = response.text

                # Extract title from markdown (first # heading)
                title = None
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                return [
                    {
                        "url": target,
                        "title": title,
                        "content": content,
                        "content_type": "markdown",
                        "status_code": response.status_code,
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                ]
        except Exception as e:
            return [
                {
                    "url": target,
                    "title": None,
                    "content": "",
                    "error": str(e),
                    "extracted_at": datetime.utcnow().isoformat(),
                }
            ]

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """Convert raw web data to UnifiedContent."""
        content = raw_data.get("content", "")
        url = raw_data.get("url", "")

        # Extract domain as author
        parsed = urlparse(url)
        domain = parsed.netloc or "unknown"

        return UnifiedContent(
            platform="web",
            source_url=url,
            author=AuthorModel(
                id=f"web_{domain}",
                platform="web",
                username=domain,
                display_name=domain,
            ),
            content=ContentModel(
                title=raw_data.get("title"),
                body=content,
                word_count=len(content.split()),
            ),
            metrics=MetricsModel(
                likes=0,
                views=0,
                comments=0,
                shares=0,
                engagement_rate=0.0,
            ),
            metadata={
                "domain": domain,
                "content_type": raw_data.get("content_type", "markdown"),
                "has_error": "error" in raw_data,
            },
        )
