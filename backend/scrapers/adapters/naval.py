"""Naval Ravikant scraper - specialized scraper for Naval's content across platforms."""

import asyncio
from datetime import datetime
from typing import List

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.youtube import YouTubeScraper


class NavalScraper(BaseScraper):
    """
    Specialized scraper for Naval Ravikant's content.

    Features:
    - Scrapes @naval tweets (wisdom, philosophy, economics)
    - Identifies and unrolls threads
    - Scrapes Naval's podcast appearances on YouTube
    - Extracts transcripts and metadata
    - Tags content with Naval-specific themes
    """

    def __init__(self):
        self.twitter_scraper = TwitterScraper()
        self.youtube_scraper = YouTubeScraper()
        self.twitter_handle = "naval"
        self.youtube_query = "Naval Ravikant podcast"

    async def health_check(self) -> dict:
        """Verify Naval scraper components are ready."""
        twitter_health = await self.twitter_scraper.health_check()
        youtube_health = await self.youtube_scraper.health_check()

        status = "ok" if twitter_health["status"] == "ok" and youtube_health["status"] == "ok" else "error"

        return {
            "status": status,
            "message": "Naval Ravikant scraper ready",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "naval",
            "components": {
                "twitter": twitter_health["status"],
                "youtube": youtube_health["status"],
            },
        }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract Naval's content from specified platform.

        Args:
            target: Platform to scrape ("twitter", "youtube", or "all")
            limit: Maximum items to fetch

        Returns:
            Raw content data from Naval's platforms
        """
        if target.lower() == "twitter":
            return await self._extract_twitter(limit)
        elif target.lower() == "youtube":
            return await self._extract_youtube(limit)
        elif target.lower() == "all":
            # Scrape both platforms in parallel
            twitter_task = self._extract_twitter(limit)
            youtube_task = self._extract_youtube(limit)
            twitter_data, youtube_data = await asyncio.gather(twitter_task, youtube_task)
            return twitter_data + youtube_data
        else:
            raise ValueError(f"Invalid target '{target}'. Use 'twitter', 'youtube', or 'all'.")

    async def _extract_twitter(self, limit: int) -> list[dict]:
        """
        Extract tweets from @naval.

        Includes:
        - Individual tweets
        - Quote tweets
        - Thread detection (for later unrolling)
        """
        print(f"🐦 Scraping @{self.twitter_handle} tweets (limit: {limit})...")

        tweets = await self.twitter_scraper.extract(f"@{self.twitter_handle}", limit=limit)

        # Add Naval-specific metadata
        for tweet in tweets:
            tweet["source"] = "naval"
            tweet["platform"] = "twitter"
            tweet["is_thread"] = self._detect_thread(tweet.get("text", ""))

        print(f"✅ Scraped {len(tweets)} tweets from @{self.twitter_handle}")
        return tweets

    async def _extract_youtube(self, limit: int) -> list[dict]:
        """
        Extract Naval's YouTube podcast appearances.

        Searches for "Naval Ravikant podcast" and extracts:
        - Transcripts
        - Video metadata
        - Podcast show notes
        """
        print(f"🎥 Scraping Naval Ravikant YouTube podcasts (limit: {limit})...")

        # Use YouTube search to find Naval podcast appearances
        # We'll use a playlist or search URL
        # For now, we'll target specific high-quality Naval content
        videos = []

        # Known Naval content sources (can be expanded)
        naval_channels = [
            # Naval himself rarely posts, but these are major podcast appearances
            "https://www.youtube.com/results?search_query=naval+ravikant+podcast",
        ]

        # For MVP, we'll extract from search results
        # In production, this would use YouTube Data API or a curated playlist
        try:
            # Extract using search query
            search_results = await self.youtube_scraper.extract(
                f"ytsearch{limit}:{self.youtube_query}",
                limit=limit
            )

            for video in search_results:
                video["source"] = "naval"
                video["platform"] = "youtube"
                videos.append(video)

            print(f"✅ Scraped {len(videos)} Naval YouTube videos")
        except Exception as e:
            print(f"⚠️  YouTube scraping error: {e}")
            # Fallback: return empty list, don't crash
            videos = []

        return videos

    def _detect_thread(self, text: str) -> bool:
        """
        Detect if a tweet is part of a thread.

        Naval's threads often contain:
        - "1/" or "1."
        - "Thread:" prefix
        - Multiple sequential numbered points
        """
        thread_indicators = [
            "1/",
            "1.",
            "Thread:",
            "🧵",
        ]

        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in thread_indicators)

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert raw Naval data to UnifiedContent.

        Delegates to platform-specific scrapers and adds Naval-specific metadata.
        """
        platform = raw_data.get("platform", "")

        if platform == "twitter":
            content = await self.twitter_scraper.normalize(raw_data)
        elif platform == "youtube":
            content = await self.youtube_scraper.normalize(raw_data)
        else:
            raise ValueError(f"Unknown platform: {platform}")

        # Add Naval-specific metadata
        content.metadata.update({
            "source": "naval",
            "is_thread": raw_data.get("is_thread", False),
            "content_type": self._classify_content_type(content.content.body),
        })

        return content

    def _classify_content_type(self, text: str) -> str:
        """
        Classify Naval's content into categories.

        Categories:
        - philosophy: Deep thinking, existential topics
        - economics: Wealth, business, investing
        - technology: Startups, coding, innovation
        - health: Meditation, fitness, longevity
        - wisdom: Short aphorisms, life advice
        """
        text_lower = text.lower()

        # Simple keyword-based classification (can be enhanced with LLM later)
        if any(word in text_lower for word in ["wealth", "money", "invest", "business", "startup"]):
            return "economics"
        elif any(word in text_lower for word in ["meditat", "health", "fitness", "sleep", "diet"]):
            return "health"
        elif any(word in text_lower for word in ["code", "programming", "technology", "software"]):
            return "technology"
        elif any(word in text_lower for word in ["meaning", "purpose", "happiness", "philosophy"]):
            return "philosophy"
        else:
            return "wisdom"

    async def scrape_naval_corpus(
        self,
        twitter_limit: int = 2000,
        youtube_limit: int = 50
    ) -> dict:
        """
        Full Naval corpus scraping with reporting.

        Args:
            twitter_limit: Max tweets to scrape (default 2000)
            youtube_limit: Max YouTube videos to scrape (default 50)

        Returns:
            Dict with scraping results and metrics
        """
        print("\n" + "="*60)
        print("🚀 NAVAL RAVIKANT CONTENT SCRAPER")
        print("="*60 + "\n")

        start_time = datetime.utcnow()
        results = {
            "twitter": [],
            "youtube": [],
            "total_items": 0,
            "credits_used": 0,
            "top_topics": [],
            "errors": [],
        }

        # Scrape Twitter
        try:
            twitter_data = await self._extract_twitter(twitter_limit)
            results["twitter"] = twitter_data
            results["total_items"] += len(twitter_data)
            # Estimate credits: ~0.01 per tweet
            results["credits_used"] += len(twitter_data) * 0.01
        except Exception as e:
            error_msg = f"Twitter scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)

        # Scrape YouTube
        try:
            youtube_data = await self._extract_youtube(youtube_limit)
            results["youtube"] = youtube_data
            results["total_items"] += len(youtube_data)
            # Estimate credits: ~1.0 per video (transcript extraction)
            results["credits_used"] += len(youtube_data) * 1.0
        except Exception as e:
            error_msg = f"YouTube scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)

        # Analyze top topics
        all_content = results["twitter"] + results["youtube"]
        topic_counts = {}
        for item in all_content:
            if "text" in item:
                content_type = self._classify_content_type(item["text"])
            elif "transcript" in item:
                content_type = self._classify_content_type(item["transcript"])
            else:
                continue

            topic_counts[content_type] = topic_counts.get(content_type, 0) + 1

        # Sort topics by frequency
        results["top_topics"] = sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"✅ Tweets scraped: {len(results['twitter'])}")
        print(f"✅ Podcasts scraped: {len(results['youtube'])}")
        print(f"✅ Total items: {results['total_items']}")
        print(f"💰 Credits used: {results['credits_used']:.2f}")
        print(f"⏱️  Duration: {duration:.2f}s")
        print("\n📌 Top Topics:")
        for topic, count in results["top_topics"]:
            print(f"   • {topic.capitalize()}: {count} items")

        if results["errors"]:
            print("\n⚠️  Errors:")
            for error in results["errors"]:
                print(f"   • {error}")

        print("\n" + "="*60)

        return results
