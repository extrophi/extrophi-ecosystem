"""Dan Koe multi-platform content scraper orchestrator."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.db.connection import get_session
from backend.db.repository import AuthorRepository, ContentRepository
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.web import WebScraper
from backend.scrapers.adapters.youtube import YouTubeScraper
from backend.scrapers.base import BaseScraper, UnifiedContent


class DanKoeScraper(BaseScraper):
    """
    Dan Koe content scraper orchestrator.

    Scrapes content from three platforms:
    1. YouTube: @thedankoe channel (all videos)
    2. Twitter/X: @thedankoe profile (last 1,000 tweets)
    3. Substack: dankoe.substack.com (all articles)

    Features:
    - Credit tracking (max 1,000 budget)
    - Database persistence
    - Comprehensive error reporting
    - Platform-specific metrics
    """

    # Platform targets
    YOUTUBE_HANDLE = "@thedankoe"
    TWITTER_HANDLE = "thedankoe"
    SUBSTACK_URL = "https://dankoe.substack.com"

    # Scraping limits
    YOUTUBE_LIMIT = 100  # videos
    TWITTER_LIMIT = 1000  # tweets
    SUBSTACK_LIMIT = 50  # articles (estimated)

    # Credit costs (estimated)
    YOUTUBE_COST_PER_VIDEO = 1  # Transcript API is free, minimal cost
    TWITTER_COST_PER_TWEET = 0.5  # Playwright scraping
    SUBSTACK_COST_PER_ARTICLE = 1  # Jina.ai free tier

    def __init__(self, max_credits: int = 1000):
        """
        Initialize Dan Koe scraper.

        Args:
            max_credits: Maximum credits to spend (default 1000)
        """
        self.max_credits = max_credits
        self.credits_used = 0

        # Initialize platform scrapers
        self.youtube_scraper = YouTubeScraper()
        self.twitter_scraper = TwitterScraper()
        self.web_scraper = WebScraper()

        # Statistics tracking
        self.stats = {
            "youtube": {"scraped": 0, "saved": 0, "errors": 0, "error_details": []},
            "twitter": {"scraped": 0, "saved": 0, "errors": 0, "error_details": []},
            "substack": {"scraped": 0, "saved": 0, "errors": 0, "error_details": []},
        }

    async def health_check(self) -> dict:
        """Check all platform scrapers."""
        youtube_health = await self.youtube_scraper.health_check()
        twitter_health = await self.twitter_scraper.health_check()
        web_health = await self.web_scraper.health_check()

        all_ok = all(
            h["status"] == "ok"
            for h in [youtube_health, twitter_health, web_health]
        )

        return {
            "status": "ok" if all_ok else "partial",
            "message": "Dan Koe scraper initialized",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "dan_koe",
            "scrapers": {
                "youtube": youtube_health,
                "twitter": twitter_health,
                "web": web_health,
            },
        }

    async def extract(self, target: str = "all", limit: int = 0) -> List[dict]:
        """
        Extract Dan Koe content from all platforms.

        Args:
            target: Platform to scrape ("all", "youtube", "twitter", "substack")
            limit: Override default limits (0 = use defaults)

        Returns:
            List of raw content dicts from all platforms
        """
        all_content = []

        # Determine which platforms to scrape
        platforms = ["youtube", "twitter", "substack"] if target == "all" else [target]

        for platform in platforms:
            if self._check_credit_limit():
                break

            if platform == "youtube":
                content = await self._scrape_youtube(limit or self.YOUTUBE_LIMIT)
                all_content.extend(content)
            elif platform == "twitter":
                content = await self._scrape_twitter(limit or self.TWITTER_LIMIT)
                all_content.extend(content)
            elif platform == "substack":
                content = await self._scrape_substack(limit or self.SUBSTACK_LIMIT)
                all_content.extend(content)

        return all_content

    async def _scrape_youtube(self, limit: int) -> List[dict]:
        """Scrape YouTube videos from @thedankoe channel."""
        print(f"\n🎥 Scraping YouTube: {self.YOUTUBE_HANDLE} (limit: {limit})")

        try:
            # YouTube handles can be passed directly
            raw_videos = await self.youtube_scraper.extract(
                self.YOUTUBE_HANDLE,
                limit=limit
            )

            self.stats["youtube"]["scraped"] = len(raw_videos)

            # Update credits
            cost = len(raw_videos) * self.YOUTUBE_COST_PER_VIDEO
            self._consume_credits(cost)

            print(f"✅ Scraped {len(raw_videos)} YouTube videos (cost: {cost} credits)")

            return raw_videos

        except Exception as e:
            error_msg = f"YouTube scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats["youtube"]["errors"] += 1
            self.stats["youtube"]["error_details"].append(error_msg)
            return []

    async def _scrape_twitter(self, limit: int) -> List[dict]:
        """Scrape tweets from @thedankoe profile."""
        print(f"\n🐦 Scraping Twitter: @{self.TWITTER_HANDLE} (limit: {limit})")

        try:
            raw_tweets = await self.twitter_scraper.extract(
                self.TWITTER_HANDLE,
                limit=limit
            )

            self.stats["twitter"]["scraped"] = len(raw_tweets)

            # Update credits
            cost = len(raw_tweets) * self.TWITTER_COST_PER_TWEET
            self._consume_credits(cost)

            print(f"✅ Scraped {len(raw_tweets)} tweets (cost: {cost} credits)")

            return raw_tweets

        except Exception as e:
            error_msg = f"Twitter scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats["twitter"]["errors"] += 1
            self.stats["twitter"]["error_details"].append(error_msg)
            return []

    async def _scrape_substack(self, limit: int) -> List[dict]:
        """Scrape articles from dankoe.substack.com."""
        print(f"\n📝 Scraping Substack: {self.SUBSTACK_URL} (limit: {limit})")

        # Substack requires discovering article URLs first
        # We'll scrape the archive page to find article links
        try:
            # First, get the archive page
            archive_url = f"{self.SUBSTACK_URL}/archive"
            archive_data = await self.web_scraper.extract(archive_url, limit=1)

            if not archive_data or not archive_data[0].get("content"):
                raise Exception("Failed to fetch Substack archive")

            # Parse markdown to extract article URLs
            article_urls = self._extract_substack_urls(
                archive_data[0]["content"],
                limit
            )

            print(f"Found {len(article_urls)} Substack articles to scrape")

            # Scrape each article
            articles = []
            for url in article_urls:
                if self._check_credit_limit():
                    break

                try:
                    article_data = await self.web_scraper.extract(url, limit=1)
                    if article_data and article_data[0].get("content"):
                        articles.append(article_data[0])

                        # Update credits per article
                        self._consume_credits(self.SUBSTACK_COST_PER_ARTICLE)

                except Exception as e:
                    error_msg = f"Failed to scrape {url}: {str(e)}"
                    self.stats["substack"]["error_details"].append(error_msg)
                    self.stats["substack"]["errors"] += 1

            self.stats["substack"]["scraped"] = len(articles)
            print(f"✅ Scraped {len(articles)} Substack articles")

            return articles

        except Exception as e:
            error_msg = f"Substack scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats["substack"]["errors"] += 1
            self.stats["substack"]["error_details"].append(error_msg)
            return []

    def _extract_substack_urls(self, markdown_content: str, limit: int) -> List[str]:
        """
        Extract article URLs from Substack archive markdown.

        Args:
            markdown_content: Markdown content from archive page
            limit: Maximum URLs to extract

        Returns:
            List of article URLs
        """
        import re

        # Substack article URLs follow pattern: https://*.substack.com/p/*
        pattern = r'https://[^/]+\.substack\.com/p/[^)\s]+'
        urls = re.findall(pattern, markdown_content)

        # Deduplicate and limit
        unique_urls = list(dict.fromkeys(urls))[:limit]

        return unique_urls

    def _consume_credits(self, amount: float):
        """Consume credits and track usage."""
        self.credits_used += amount

    def _check_credit_limit(self) -> bool:
        """Check if credit limit has been reached."""
        if self.credits_used >= self.max_credits:
            print(f"⚠️  Credit limit reached: {self.credits_used}/{self.max_credits}")
            return True
        return False

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Normalize raw content to UnifiedContent schema.

        This method delegates to the appropriate platform scraper.
        """
        # Determine platform from raw_data
        if "video_id" in raw_data:
            return await self.youtube_scraper.normalize(raw_data)
        elif "tweet_id" in raw_data or "author_id" in raw_data:
            return await self.twitter_scraper.normalize(raw_data)
        else:
            return await self.web_scraper.normalize(raw_data)

    async def scrape_and_save(self, target: str = "all") -> Dict[str, Any]:
        """
        Scrape Dan Koe content and save to database.

        Args:
            target: Platform to scrape ("all", "youtube", "twitter", "substack")

        Returns:
            Report with statistics and errors
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting Dan Koe Content Scraper")
        print(f"{'='*60}")
        print(f"Target: {target}")
        print(f"Max credits: {self.max_credits}")
        print(f"{'='*60}\n")

        # Extract raw content
        raw_content = await self.extract(target)

        print(f"\n{'='*60}")
        print(f"📊 Saving to database...")
        print(f"{'='*60}\n")

        # Save to database
        db_gen = get_session()
        db = next(db_gen)

        try:
            content_repo = ContentRepository(db)
            author_repo = AuthorRepository(db)

            # Create/update Dan Koe author entries for each platform
            authors = {}
            if target == "all" or target == "youtube":
                authors["youtube"] = author_repo.create(
                    author_id="youtube_dan_koe",
                    platform="youtube",
                    username="thedankoe",
                    display_name="Dan Koe",
                    profile_url=f"https://youtube.com/{self.YOUTUBE_HANDLE}",
                )

            if target == "all" or target == "twitter":
                authors["twitter"] = author_repo.create(
                    author_id="twitter_dan_koe",
                    platform="twitter",
                    username="thedankoe",
                    display_name="Dan Koe",
                    profile_url=f"https://twitter.com/{self.TWITTER_HANDLE}",
                )

            if target == "all" or target == "substack":
                authors["substack"] = author_repo.create(
                    author_id="web_dankoe.substack.com",
                    platform="web",
                    username="dankoe",
                    display_name="Dan Koe",
                    profile_url=self.SUBSTACK_URL,
                )

            # Normalize and save each piece of content
            for raw in raw_content:
                try:
                    # Normalize to UnifiedContent
                    unified = await self.normalize(raw)

                    # Determine platform
                    platform = unified.platform

                    # Check if already exists
                    existing = content_repo.get_by_url(unified.source_url)
                    if existing:
                        print(f"⏭️  Skipping duplicate: {unified.source_url}")
                        continue

                    # Save to database
                    content_repo.create(
                        platform=unified.platform,
                        source_url=unified.source_url,
                        author_id=unified.author.id,
                        content_body=unified.content.body,
                        content_title=unified.content.title,
                        metrics=unified.metrics.dict(),
                        metadata=unified.metadata,
                    )

                    # Update stats
                    self.stats[platform]["saved"] += 1
                    print(f"✅ Saved: {unified.source_url[:60]}...")

                except Exception as e:
                    error_msg = f"Failed to save content: {str(e)}"
                    print(f"❌ {error_msg}")
                    # Try to determine platform from raw data
                    if "video_id" in raw:
                        self.stats["youtube"]["error_details"].append(error_msg)
                        self.stats["youtube"]["errors"] += 1
                    elif "tweet_id" in raw or "author_id" in raw:
                        self.stats["twitter"]["error_details"].append(error_msg)
                        self.stats["twitter"]["errors"] += 1
                    else:
                        self.stats["substack"]["error_details"].append(error_msg)
                        self.stats["substack"]["errors"] += 1

        finally:
            db_gen.close()

        # Generate final report
        report = self._generate_report()

        print(f"\n{'='*60}")
        print(f"📋 FINAL REPORT")
        print(f"{'='*60}")
        print(report["summary"])
        print(f"\n{'='*60}\n")

        return report

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive scraping report."""
        total_scraped = sum(s["scraped"] for s in self.stats.values())
        total_saved = sum(s["saved"] for s in self.stats.values())
        total_errors = sum(s["errors"] for s in self.stats.values())

        summary = f"""
Dan Koe Content Scraper Report
Generated: {datetime.utcnow().isoformat()}

TOTALS:
  Total Items Scraped: {total_scraped}
  Total Items Saved:   {total_saved}
  Total Errors:        {total_errors}
  Credits Used:        {self.credits_used:.2f} / {self.max_credits}

PLATFORM BREAKDOWN:

YouTube (@thedankoe):
  Scraped: {self.stats['youtube']['scraped']}
  Saved:   {self.stats['youtube']['saved']}
  Errors:  {self.stats['youtube']['errors']}

Twitter (@thedankoe):
  Scraped: {self.stats['twitter']['scraped']}
  Saved:   {self.stats['twitter']['saved']}
  Errors:  {self.stats['twitter']['errors']}

Substack (dankoe.substack.com):
  Scraped: {self.stats['substack']['scraped']}
  Saved:   {self.stats['substack']['saved']}
  Errors:  {self.stats['substack']['errors']}
"""

        # Add error details if any
        if total_errors > 0:
            summary += "\nERROR DETAILS:\n"
            for platform, stats in self.stats.items():
                if stats["errors"] > 0:
                    summary += f"\n{platform.upper()}:\n"
                    for error in stats["error_details"][:5]:  # Limit to 5 errors
                        summary += f"  - {error}\n"

        return {
            "summary": summary,
            "stats": self.stats,
            "credits_used": self.credits_used,
            "total_scraped": total_scraped,
            "total_saved": total_saved,
            "total_errors": total_errors,
        }
