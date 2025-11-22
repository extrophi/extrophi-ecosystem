"""
Alex Hormozi content scraper - Multi-platform orchestrator for business/marketing insights.

Targets:
- YouTube: @AlexHormozi channel (videos, transcripts, business frameworks)
- Twitter/X: @AlexHormozi (marketing insights, sales processes)

Focus Areas:
- Marketing frameworks
- Sales processes
- Business scaling concepts
- Offer creation strategies
- Value ladders
"""

import asyncio
from datetime import datetime
from typing import Any

from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.youtube import YouTubeScraper
from backend.scrapers.base import (
    AnalysisModel,
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class HormoziScraper(BaseScraper):
    """
    Multi-platform scraper for Alex Hormozi's business/marketing content.

    Orchestrates YouTube and Twitter scrapers to collect comprehensive
    content about marketing frameworks, sales processes, and business scaling.

    Features:
    - Channel-wide YouTube scraping (@AlexHormozi)
    - Twitter timeline scraping (@AlexHormozi)
    - Unified content aggregation
    - Marketing framework extraction
    - Engagement metrics tracking
    """

    # Alex Hormozi's platform identifiers
    YOUTUBE_CHANNEL = "https://www.youtube.com/@AlexHormozi"
    TWITTER_USERNAME = "AlexHormozi"

    # Marketing frameworks to track
    FRAMEWORKS = [
        "value ladder",
        "grand slam offer",
        "lead magnet",
        "irresistible offer",
        "pricing strategy",
        "customer acquisition",
        "ltv",
        "lifetime value",
        "conversion rate",
        "sales script",
        "close rate",
        "objection handling",
        "scarcity",
        "urgency",
        "guarantee",
        "risk reversal",
        "value equation",
        "dream outcome",
        "perceived likelihood",
        "time delay",
        "effort & sacrifice",
    ]

    def __init__(self):
        """Initialize YouTube and Twitter scrapers."""
        self.youtube = YouTubeScraper()
        self.twitter = TwitterScraper()
        self.total_credits_used = 0
        self.max_credits = 1000

    async def health_check(self) -> dict:
        """Verify both YouTube and Twitter scrapers are ready."""
        youtube_health = await self.youtube.health_check()
        twitter_health = await self.twitter.health_check()

        all_ok = (
            youtube_health["status"] == "ok" and
            twitter_health["status"] == "ok"
        )

        return {
            "status": "ok" if all_ok else "error",
            "message": "Hormozi scraper ready" if all_ok else "One or more scrapers failed",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "hormozi",
            "scrapers": {
                "youtube": youtube_health,
                "twitter": twitter_health,
            },
        }

    async def extract(self, target: str = "all", limit: int = 20) -> list[dict]:
        """
        Extract content from Alex Hormozi's platforms.

        Args:
            target: Platform to scrape ("youtube", "twitter", or "all")
            limit: Maximum items per platform

        Returns:
            Raw content data with platform identifiers
        """
        results = []

        if target in ("all", "youtube"):
            youtube_data = await self._extract_youtube(limit)
            results.extend(youtube_data)

        if target in ("all", "twitter"):
            twitter_data = await self._extract_twitter(limit)
            results.extend(twitter_data)

        return results

    async def _extract_youtube(self, limit: int) -> list[dict]:
        """Extract videos from Alex Hormozi's YouTube channel."""
        try:
            print(f"🎥 Scraping YouTube: {self.YOUTUBE_CHANNEL} (limit: {limit})")

            # Extract from channel
            videos = await self.youtube.extract(
                target=self.YOUTUBE_CHANNEL,
                limit=limit
            )

            # Add source identifier
            for video in videos:
                video["source"] = "hormozi"
                video["platform"] = "youtube"

            print(f"✅ YouTube: {len(videos)} videos extracted")
            return videos

        except Exception as e:
            print(f"❌ YouTube extraction failed: {e}")
            return []

    async def _extract_twitter(self, limit: int) -> list[dict]:
        """Extract tweets from Alex Hormozi's Twitter profile."""
        try:
            print(f"🐦 Scraping Twitter: @{self.TWITTER_USERNAME} (limit: {limit})")

            # Extract tweets
            tweets = await self.twitter.extract(
                target=self.TWITTER_USERNAME,
                limit=limit
            )

            # Add source identifier
            for tweet in tweets:
                tweet["source"] = "hormozi"
                tweet["platform"] = "twitter"

            print(f"✅ Twitter: {len(tweets)} tweets extracted")
            return tweets

        except Exception as e:
            print(f"❌ Twitter extraction failed: {e}")
            return []

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert platform-specific data to UnifiedContent with Hormozi-specific analysis.

        Routes to the appropriate platform normalizer and enhances with
        marketing framework detection.
        """
        platform = raw_data.get("platform", "unknown")

        # Route to appropriate normalizer
        if platform == "youtube":
            content = await self.youtube.normalize(raw_data)
        elif platform == "twitter":
            content = await self.twitter.normalize(raw_data)
        else:
            raise ValueError(f"Unknown platform: {platform}")

        # Enhance with Hormozi-specific analysis
        content = await self._enhance_with_frameworks(content)

        # Add source metadata
        content.metadata["source"] = "hormozi"
        content.metadata["author"] = "Alex Hormozi"
        content.metadata["content_type"] = "business_marketing"

        return content

    async def _enhance_with_frameworks(self, content: UnifiedContent) -> UnifiedContent:
        """
        Detect marketing frameworks in content.

        Scans content for Hormozi's signature frameworks and business concepts.
        """
        text = content.content.body.lower()
        detected_frameworks = []

        # Detect frameworks by keyword matching
        for framework in self.FRAMEWORKS:
            if framework.lower() in text:
                detected_frameworks.append(framework)

        # Add to analysis
        content.analysis.frameworks = detected_frameworks

        # Extract common themes
        themes = []
        if any(kw in text for kw in ["offer", "pricing", "value"]):
            themes.append("offer_creation")
        if any(kw in text for kw in ["sales", "close", "conversion"]):
            themes.append("sales_process")
        if any(kw in text for kw in ["scale", "growth", "acquisition"]):
            themes.append("business_scaling")
        if any(kw in text for kw in ["ad", "marketing", "funnel"]):
            themes.append("marketing_strategy")

        content.analysis.themes = themes

        # Detect hooks (common Hormozi patterns)
        hooks = []
        if "how to" in text:
            hooks.append("educational_hook")
        if any(kw in text for kw in ["mistake", "avoid", "wrong"]):
            hooks.append("mistake_avoidance")
        if any(kw in text for kw in ["secret", "nobody tells you", "truth"]):
            hooks.append("insider_knowledge")
        if text.startswith(("if you", "when you", "stop")):
            hooks.append("direct_address")

        content.analysis.hooks = hooks

        return content

    async def scrape_all(
        self,
        youtube_limit: int = 50,
        twitter_limit: int = 1000,
    ) -> dict[str, Any]:
        """
        Comprehensive scraping of all Alex Hormozi content.

        Args:
            youtube_limit: Max YouTube videos to scrape
            twitter_limit: Max tweets to scrape

        Returns:
            Summary report with:
            - videos_scraped: int
            - tweets_scraped: int
            - frameworks_identified: list[str]
            - content: list[UnifiedContent]
            - credits_used: int
        """
        print("🚀 Starting comprehensive Hormozi content scrape...")
        print(f"   YouTube limit: {youtube_limit}")
        print(f"   Twitter limit: {twitter_limit}")
        print(f"   Max credits: {self.max_credits}")
        print()

        # Extract raw data from both platforms
        raw_youtube = await self._extract_youtube(youtube_limit)
        raw_twitter = await self._extract_twitter(twitter_limit)

        all_raw_data = raw_youtube + raw_twitter

        # Normalize all content
        print("\n📊 Normalizing content...")
        normalized_content = []

        for raw_item in all_raw_data:
            try:
                unified = await self.normalize(raw_item)
                normalized_content.append(unified)
            except Exception as e:
                print(f"⚠️  Failed to normalize item: {e}")
                continue

        # Aggregate framework insights
        all_frameworks = set()
        all_themes = set()
        all_hooks = set()

        for content in normalized_content:
            all_frameworks.update(content.analysis.frameworks)
            all_themes.update(content.analysis.themes)
            all_hooks.update(content.analysis.hooks)

        # Calculate credits (rough estimate: 1 credit per item)
        credits_used = len(normalized_content)
        self.total_credits_used = credits_used

        # Generate report
        report = {
            "summary": {
                "videos_scraped": len(raw_youtube),
                "tweets_scraped": len(raw_twitter),
                "total_items": len(normalized_content),
                "credits_used": credits_used,
                "credits_remaining": self.max_credits - credits_used,
            },
            "insights": {
                "frameworks_identified": sorted(all_frameworks),
                "themes_identified": sorted(all_themes),
                "hooks_identified": sorted(all_hooks),
                "framework_count": len(all_frameworks),
                "theme_count": len(all_themes),
            },
            "content": normalized_content,
            "platform_breakdown": {
                "youtube": {
                    "count": len(raw_youtube),
                    "total_views": sum(
                        item.get("view_count", 0) for item in raw_youtube
                    ),
                    "total_likes": sum(
                        item.get("like_count", 0) for item in raw_youtube
                    ),
                },
                "twitter": {
                    "count": len(raw_twitter),
                    "total_likes": sum(
                        item.get("public_metrics", {}).get("like_count", 0)
                        for item in raw_twitter
                    ),
                    "total_retweets": sum(
                        item.get("public_metrics", {}).get("retweet_count", 0)
                        for item in raw_twitter
                    ),
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Print summary
        print("\n" + "="*60)
        print("📈 SCRAPING COMPLETE - HORMOZI CONTENT REPORT")
        print("="*60)
        print(f"\n📊 Content Collected:")
        print(f"   • YouTube videos: {report['summary']['videos_scraped']}")
        print(f"   • Twitter posts: {report['summary']['tweets_scraped']}")
        print(f"   • Total items: {report['summary']['total_items']}")

        print(f"\n💡 Marketing Insights:")
        print(f"   • Frameworks identified: {report['insights']['framework_count']}")
        print(f"   • Themes detected: {report['insights']['theme_count']}")
        print(f"   • Hook patterns: {len(all_hooks)}")

        if all_frameworks:
            print(f"\n🎯 Top Frameworks Detected:")
            for framework in sorted(all_frameworks)[:10]:
                print(f"      - {framework}")

        print(f"\n💰 Credits:")
        print(f"   • Used: {report['summary']['credits_used']}")
        print(f"   • Remaining: {report['summary']['credits_remaining']}")
        print(f"   • Budget: {self.max_credits}")

        print("\n" + "="*60)

        return report
