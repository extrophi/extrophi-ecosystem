"""Daniel Throssell scraper combining Twitter and website content."""

import os
from datetime import datetime
from typing import Any

import httpx

from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.web import WebScraper
from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class ThrossellScraper(BaseScraper):
    """
    Specialized scraper for Daniel Throssell's copywriting content.

    Targets:
    1. Twitter @danielthrossell - Last 2,000 tweets (email marketing insights, copywriting tips)
    2. Website persuasivepage.com - Blog posts, email examples, copywriting templates
    3. Personal site danielthrossell.com

    Focus areas:
    - Copywriting techniques
    - Email marketing procedures
    - Persuasion frameworks (AIDA, PAS, PASTOR, etc.)
    - Voice of Customer (VOC) patterns
    - Hook extraction methods

    All content stored with:
    - source="throssell"
    - platform="twitter" or "website"
    - Rich metadata for copywriting analysis
    """

    # Twitter username
    TWITTER_USERNAME = "danielthrossell"

    # Websites to scrape
    WEBSITES = [
        "https://persuasivepage.com/",
        "https://danielthrossell.com/",
    ]

    # Blog/article paths (discovered from web research)
    BLOG_PATHS = [
        "https://persuasivepage.com/compendium/",  # Email Copywriting Compendium
        "https://persuasivepage.com/products/",  # CopyMart products
    ]

    def __init__(self) -> None:
        """Initialize with Twitter and Web scrapers."""
        self.twitter_scraper = TwitterScraper()
        self.web_scraper = WebScraper()
        self.source = "throssell"
        self.credits_used = 0

    async def health_check(self) -> dict:
        """Verify all scraper components are working."""
        twitter_health = await self.twitter_scraper.health_check()
        web_health = await self.web_scraper.health_check()

        all_healthy = twitter_health["status"] == "ok" and web_health["status"] == "ok"

        return {
            "status": "ok" if all_healthy else "degraded",
            "message": f"Throssell scraper ready - Twitter: {twitter_health['status']}, Web: {web_health['status']}",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "throssell",
            "components": {
                "twitter": twitter_health,
                "web": web_health,
            },
        }

    async def extract(self, target: str = "all", limit: int = 2000) -> list[dict]:
        """
        Extract content from Daniel Throssell's platforms.

        Args:
            target: What to scrape
                - "all" (default): Twitter + websites
                - "twitter": Just Twitter
                - "website": Just websites
                - URL: Specific URL
            limit: Max tweets to fetch (default 2000)

        Returns:
            Combined list of raw content from all sources
        """
        all_content = []

        # Scrape Twitter
        if target in ["all", "twitter"]:
            print(f"🐦 Scraping Twitter @{self.TWITTER_USERNAME} (limit: {limit})...")
            twitter_data = await self.twitter_scraper.extract(self.TWITTER_USERNAME, limit=limit)

            # Add source metadata
            for tweet in twitter_data:
                tweet["_source"] = self.source
                tweet["_platform"] = "twitter"

            all_content.extend(twitter_data)
            self.credits_used += len(twitter_data) * 0.5  # Estimate
            print(f"✅ Scraped {len(twitter_data)} tweets")

        # Scrape websites
        if target in ["all", "website"]:
            print(f"🌐 Scraping websites...")
            website_data = await self._scrape_websites()

            # Add source metadata
            for page in website_data:
                page["_source"] = self.source
                page["_platform"] = "website"

            all_content.extend(website_data)
            print(f"✅ Scraped {len(website_data)} web pages")

        # Scrape specific URL
        if target.startswith("http"):
            print(f"🔗 Scraping specific URL: {target}")
            url_data = await self.web_scraper.extract(target)

            for page in url_data:
                page["_source"] = self.source
                page["_platform"] = "website"

            all_content.extend(url_data)

        return all_content

    async def _scrape_websites(self) -> list[dict]:
        """Scrape all Throssell websites and blog paths."""
        all_pages = []

        # Main websites
        for url in self.WEBSITES:
            try:
                pages = await self.web_scraper.extract(url)
                all_pages.extend(pages)
                self.credits_used += 1  # Jina.ai free tier
            except Exception as e:
                print(f"⚠️  Failed to scrape {url}: {e}")

        # Blog paths
        for url in self.BLOG_PATHS:
            try:
                pages = await self.web_scraper.extract(url)
                all_pages.extend(pages)
                self.credits_used += 1
            except Exception as e:
                print(f"⚠️  Failed to scrape {url}: {e}")

        return all_pages

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert raw Throssell data to UnifiedContent with rich copywriting metadata.

        Delegates to appropriate scraper based on platform.
        """
        platform = raw_data.get("_platform", "unknown")

        # Normalize via appropriate scraper
        if platform == "twitter":
            content = await self.twitter_scraper.normalize(raw_data)
        elif platform == "website":
            content = await self.web_scraper.normalize(raw_data)
        else:
            raise ValueError(f"Unknown platform: {platform}")

        # Override with Throssell-specific metadata
        content.metadata["source"] = self.source
        content.metadata["author_name"] = "Daniel Throssell"
        content.metadata["specialization"] = "email_copywriting"
        content.metadata["focus_areas"] = [
            "copywriting_techniques",
            "email_marketing",
            "persuasion_frameworks",
            "storytelling",
            "hook_formulas",
        ]

        return content

    async def scrape_all(self, tweet_limit: int = 2000) -> dict[str, Any]:
        """
        Complete Throssell scraping workflow.

        Args:
            tweet_limit: Max tweets to scrape (default 2000)

        Returns:
            Summary with statistics and normalized content
        """
        print(f"\n{'='*60}")
        print(f"🎯 AGENT #5: DANIEL THROSSELL SCRAPER")
        print(f"{'='*60}\n")

        # Extract raw data
        raw_content = await self.extract("all", limit=tweet_limit)

        # Normalize all content
        normalized_content = []
        for item in raw_content:
            try:
                normalized = await self.normalize(item)
                normalized_content.append(normalized)
            except Exception as e:
                print(f"⚠️  Failed to normalize item: {e}")

        # Analyze copywriting patterns
        copywriting_stats = self._analyze_copywriting_patterns(normalized_content)

        # Generate report
        report = {
            "agent": "Agent #5: Daniel Throssell Scraper",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_items": len(normalized_content),
                "tweets_scraped": sum(1 for c in normalized_content if c.platform == "twitter"),
                "web_pages_scraped": sum(1 for c in normalized_content if c.platform == "web"),
                "total_words": sum(c.content.word_count for c in normalized_content),
                "credits_used": self.credits_used,
                "credits_remaining": 800 - self.credits_used,
            },
            "copywriting_insights": copywriting_stats,
            "content": normalized_content,
        }

        self._print_report(report)

        return report

    def _analyze_copywriting_patterns(self, content: list[UnifiedContent]) -> dict[str, Any]:
        """Analyze copywriting patterns in Throssell's content."""
        # Extract high-engagement tweets
        high_engagement = [
            c for c in content
            if c.platform == "twitter" and (c.metrics.likes + c.metrics.shares) > 50
        ]

        # Identify common words/phrases
        all_text = " ".join(c.content.body for c in content)
        words = all_text.lower().split()

        # Copywriting keywords
        copywriting_keywords = [
            "email", "copywriting", "persuasion", "hook", "framework",
            "conversion", "headline", "storytelling", "sales", "revenue"
        ]

        keyword_counts = {
            kw: words.count(kw)
            for kw in copywriting_keywords
        }

        return {
            "high_engagement_count": len(high_engagement),
            "avg_tweet_length": sum(c.content.word_count for c in content if c.platform == "twitter") / max(sum(1 for c in content if c.platform == "twitter"), 1),
            "copywriting_keyword_frequency": keyword_counts,
            "potential_frameworks_mentioned": keyword_counts.get("framework", 0),
        }

    def _print_report(self, report: dict) -> None:
        """Print formatted scraping report."""
        print(f"\n{'='*60}")
        print(f"📊 THROSSELL SCRAPER REPORT")
        print(f"{'='*60}\n")

        stats = report["statistics"]
        print(f"✅ Total Items: {stats['total_items']}")
        print(f"🐦 Tweets: {stats['tweets_scraped']}")
        print(f"🌐 Web Pages: {stats['web_pages_scraped']}")
        print(f"📝 Total Words: {stats['total_words']:,}")
        print(f"💰 Credits Used: {stats['credits_used']:.1f} / 800")
        print(f"💳 Credits Remaining: {stats['credits_remaining']:.1f}")

        insights = report["copywriting_insights"]
        print(f"\n{'='*60}")
        print(f"🎨 COPYWRITING INSIGHTS")
        print(f"{'='*60}\n")
        print(f"🔥 High Engagement Posts: {insights['high_engagement_count']}")
        print(f"📏 Avg Tweet Length: {insights['avg_tweet_length']:.1f} words")
        print(f"🎯 Framework Mentions: {insights['potential_frameworks_mentioned']}")

        print(f"\n{'='*60}")
        print(f"🔑 KEYWORD FREQUENCY")
        print(f"{'='*60}\n")
        for keyword, count in insights["copywriting_keyword_frequency"].items():
            if count > 0:
                print(f"  • {keyword}: {count}")

        print(f"\n{'='*60}\n")


async def main():
    """Test the Throssell scraper."""
    scraper = ThrossellScraper()

    # Health check
    health = await scraper.health_check()
    print(f"Health: {health}")

    # Run full scrape (limit to 100 tweets for testing)
    report = await scraper.scrape_all(tweet_limit=100)

    # Print sample content
    print(f"\n📄 SAMPLE CONTENT (first 3 items):\n")
    for i, item in enumerate(report["content"][:3], 1):
        print(f"{i}. [{item.platform}] {item.content.body[:100]}...")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
