#!/usr/bin/env python3
"""
Test script for Daniel Throssell scraper.

Usage:
    python test_throssell_scraper.py [--tweet-limit LIMIT] [--mode MODE]

Modes:
    - test: Quick test with 20 tweets
    - small: 100 tweets
    - medium: 500 tweets
    - full: 2000 tweets (full scrape)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scrapers.adapters.throssell import ThrossellScraper


async def main():
    parser = argparse.ArgumentParser(description="Test Daniel Throssell scraper")
    parser.add_argument(
        "--tweet-limit",
        type=int,
        default=None,
        help="Number of tweets to scrape (overrides mode)",
    )
    parser.add_argument(
        "--mode",
        choices=["test", "small", "medium", "full"],
        default="test",
        help="Scraping mode (test=20, small=100, medium=500, full=2000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="throssell_scrape_results.json",
        help="Output JSON file for results",
    )

    args = parser.parse_args()

    # Determine tweet limit
    if args.tweet_limit:
        tweet_limit = args.tweet_limit
    else:
        limits = {"test": 20, "small": 100, "medium": 500, "full": 2000}
        tweet_limit = limits[args.mode]

    print(f"\n🎯 Starting Throssell scraper in '{args.mode}' mode")
    print(f"📊 Tweet limit: {tweet_limit}")
    print(f"💾 Output file: {args.output}\n")

    # Initialize scraper
    scraper = ThrossellScraper()

    # Health check
    print("🏥 Running health check...")
    health = await scraper.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Message: {health['message']}\n")

    if health["status"] != "ok":
        print("❌ Health check failed. Aborting.")
        return

    # Run scraper
    try:
        report = await scraper.scrape_all(tweet_limit=tweet_limit)

        # Save results
        print(f"\n💾 Saving results to {args.output}...")

        # Convert UnifiedContent objects to dicts for JSON serialization
        serializable_report = {
            "agent": report["agent"],
            "timestamp": report["timestamp"],
            "statistics": report["statistics"],
            "copywriting_insights": report["copywriting_insights"],
            "content": [
                {
                    "content_id": str(c.content_id),
                    "platform": c.platform,
                    "source_url": c.source_url,
                    "author": {
                        "id": c.author.id,
                        "platform": c.author.platform,
                        "username": c.author.username,
                        "display_name": c.author.display_name,
                    },
                    "content": {
                        "title": c.content.title,
                        "body": c.content.body,
                        "word_count": c.content.word_count,
                    },
                    "metrics": {
                        "likes": c.metrics.likes,
                        "views": c.metrics.views,
                        "comments": c.metrics.comments,
                        "shares": c.metrics.shares,
                        "engagement_rate": c.metrics.engagement_rate,
                    },
                    "metadata": c.metadata,
                    "scraped_at": c.scraped_at.isoformat(),
                }
                for c in report["content"]
            ],
        }

        with open(args.output, "w") as f:
            json.dump(serializable_report, f, indent=2)

        print(f"✅ Results saved successfully!")

        # Print summary
        print(f"\n{'='*60}")
        print(f"📈 SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total items scraped: {report['statistics']['total_items']}")
        print(f"🐦 Tweets: {report['statistics']['tweets_scraped']}")
        print(f"🌐 Web pages: {report['statistics']['web_pages_scraped']}")
        print(f"📝 Total words: {report['statistics']['total_words']:,}")
        print(f"💰 Credits used: {report['statistics']['credits_used']:.1f}")
        print(f"💳 Credits remaining: {report['statistics']['credits_remaining']:.1f}")
        print(f"{'='*60}\n")

        # Sample content
        if report["content"]:
            print(f"📄 SAMPLE CONTENT (first 3 items):\n")
            for i, item in enumerate(report["content"][:3], 1):
                preview = item.content.body[:150].replace("\n", " ")
                print(f"{i}. [{item.platform}] {preview}...")
                print(f"   📊 Likes: {item.metrics.likes}, Comments: {item.metrics.comments}")
                print()

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
