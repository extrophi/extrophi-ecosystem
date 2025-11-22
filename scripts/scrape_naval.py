#!/usr/bin/env python3
"""
Script to scrape Naval Ravikant's content from Twitter and YouTube.

Usage:
    python scripts/scrape_naval.py --twitter-limit 2000 --youtube-limit 50
    python scripts/scrape_naval.py --platform twitter --limit 100
    python scripts/scrape_naval.py --platform youtube --limit 20
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.adapters.naval import NavalScraper


async def main():
    parser = argparse.ArgumentParser(description="Scrape Naval Ravikant's content")
    parser.add_argument(
        "--platform",
        choices=["twitter", "youtube", "all"],
        default="all",
        help="Platform to scrape (default: all)",
    )
    parser.add_argument(
        "--twitter-limit",
        type=int,
        default=2000,
        help="Maximum tweets to scrape (default: 2000)",
    )
    parser.add_argument(
        "--youtube-limit",
        type=int,
        default=50,
        help="Maximum YouTube videos to scrape (default: 50)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Universal limit for all platforms (overrides platform-specific limits)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path (optional)",
    )

    args = parser.parse_args()

    # Use universal limit if specified
    twitter_limit = args.limit if args.limit else args.twitter_limit
    youtube_limit = args.limit if args.limit else args.youtube_limit

    # Create scraper
    scraper = NavalScraper()

    # Run health check
    print("🔍 Running health check...")
    health = await scraper.health_check()
    print(f"Status: {health['status']}")
    print(f"Components: {health['components']}\n")

    if health["status"] != "ok":
        print("❌ Health check failed. Exiting.")
        sys.exit(1)

    # Run scraper based on platform
    if args.platform == "all":
        results = await scraper.scrape_naval_corpus(
            twitter_limit=twitter_limit,
            youtube_limit=youtube_limit
        )
    else:
        print(f"\n🚀 Scraping Naval's {args.platform} content...\n")
        limit = twitter_limit if args.platform == "twitter" else youtube_limit
        data = await scraper.extract(args.platform, limit=limit)

        results = {
            "platform": args.platform,
            "items": data,
            "total_items": len(data),
        }

        print(f"\n✅ Scraped {len(data)} items from {args.platform}")

    # Save to file if requested
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {output_path}")

    print("\n✨ Done!\n")


if __name__ == "__main__":
    asyncio.run(main())
