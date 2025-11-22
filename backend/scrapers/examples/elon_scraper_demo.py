#!/usr/bin/env python3
"""
Elon Musk Scraper Demo

Usage:
    python -m backend.scrapers.examples.elon_scraper_demo [--limit 100]

Requirements:
    - twscrape installed (uv pip install twscrape)
    - twscrape account configured (optional, works without auth for public data)

Output:
    - JSON file with scraped tweets
    - Statistics report (meme ratio, themes, top insights)
"""

import argparse
import asyncio
import json
from pathlib import Path

from backend.scrapers.elon import ElonScraper


async def main():
    """Run Elon Musk scraper and generate report."""
    parser = argparse.ArgumentParser(description="Scrape @elonmusk tweets for innovation insights")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of tweets to scrape (max 1000, default 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="elon_tweets.json",
        help="Output JSON file path",
    )
    args = parser.parse_args()

    # Initialize scraper
    print("🚀 Initializing Elon Musk scraper...")
    scraper = ElonScraper()

    # Health check
    health = await scraper.health_check()
    print(f"✅ {health['message']}")
    print(f"📊 Max tweets: {health['max_tweets']}")
    print()

    # Extract tweets
    limit = min(args.limit, 1000)  # Cap at 1,000
    print(f"🔍 Scraping last {limit} tweets from @elonmusk...")
    print("⏳ This may take a while (human-like scraping to avoid rate limits)...")
    print()

    try:
        raw_tweets = await scraper.extract(target="elonmusk", limit=limit)
        print(f"✅ Scraped {len(raw_tweets)} tweets")
    except Exception as e:
        print(f"❌ Error scraping tweets: {e}")
        print("💡 Note: twscrape requires account setup for large-scale scraping")
        print("   For demo purposes, using mock data...")
        raw_tweets = _get_mock_tweets()

    # Normalize and categorize
    print("\n🧠 Analyzing tweets (innovation vs memes, theme detection)...")
    normalized_tweets = []

    for tweet in raw_tweets:
        normalized = await scraper.normalize(tweet)
        normalized_tweets.append(normalized.model_dump())

    # Get statistics
    stats = scraper.get_stats()

    # Generate report
    print("\n" + "=" * 60)
    print("📈 ELON MUSK TWEET ANALYSIS REPORT")
    print("=" * 60)
    print(f"\n📊 Total Scraped: {stats['total_scraped']} tweets")
    print(f"\n💡 Innovation/Insights: {stats['innovation']} ({100 - float(stats['meme_ratio'].rstrip('%')):.1f}%)")
    print(f"😂 Memes/Jokes: {stats['memes']} ({stats['meme_ratio']})")
    print(f"\n🎯 Top Theme: {stats['top_theme'].upper()}")
    print("\n📚 Theme Breakdown:")
    for theme, count in sorted(stats['themes'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / stats['total_scraped'] * 100) if stats['total_scraped'] > 0 else 0
            print(f"   • {theme.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    # Sample insights
    print("\n🌟 Sample Innovation Insights:")
    innovation_tweets = [
        t for t in normalized_tweets
        if t['metadata'].get('category') == 'innovation'
    ][:5]

    for i, tweet in enumerate(innovation_tweets, 1):
        text = tweet['content']['body'][:100] + "..." if len(tweet['content']['body']) > 100 else tweet['content']['body']
        themes = ", ".join(tweet['metadata']['themes'][:3])
        print(f"   {i}. [{themes}] {text}")

    # Sample memes
    print("\n😂 Sample Memes (for the culture):")
    meme_tweets = [
        t for t in normalized_tweets
        if t['metadata'].get('category') == 'meme'
    ][:3]

    for i, tweet in enumerate(meme_tweets, 1):
        text = tweet['content']['body'][:100] + "..." if len(tweet['content']['body']) > 100 else tweet['content']['body']
        print(f"   {i}. {text}")

    print("\n" + "=" * 60)

    # Save to JSON
    output_path = Path(args.output)
    output_data = {
        "metadata": {
            "source": "elonmusk",
            "platform": "twitter",
            "scraped_at": health["timestamp"],
            "total_tweets": len(normalized_tweets),
        },
        "statistics": stats,
        "tweets": normalized_tweets,
    }

    output_path.write_text(json.dumps(output_data, indent=2, default=str))
    print(f"\n💾 Results saved to: {output_path}")
    print(f"📊 File size: {output_path.stat().st_size / 1024:.1f} KB")

    # Credits estimate (mock - twscrape is free)
    print(f"\n💰 Credits Used: 0 (twscrape is FREE!)")
    print(f"💸 Cost: $0.00 (no API required)")

    print("\n✨ Analysis complete!")


def _get_mock_tweets():
    """Mock tweets for demo/testing when twscrape is not configured."""
    return [
        {
            "id": "1",
            "text": "Tesla's new battery tech achieves 500 Wh/kg using first principles optimization",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T10:00:00Z",
            "public_metrics": {"like_count": 50000, "retweet_count": 10000, "reply_count": 2000, "view_count": 1000000},
            "url": "https://twitter.com/elonmusk/status/1",
            "is_retweet": False,
            "is_reply": False,
        },
        {
            "id": "2",
            "text": "Starship launch was incredible. Mars, here we come! 🚀",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T11:00:00Z",
            "public_metrics": {"like_count": 80000, "retweet_count": 15000, "reply_count": 3000, "view_count": 2000000},
            "url": "https://twitter.com/elonmusk/status/2",
            "is_retweet": False,
            "is_reply": False,
        },
        {
            "id": "3",
            "text": "lmao 😂😂😂",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T12:00:00Z",
            "public_metrics": {"like_count": 30000, "retweet_count": 5000, "reply_count": 1000, "view_count": 500000},
            "url": "https://twitter.com/elonmusk/status/3",
            "is_retweet": False,
            "is_reply": False,
        },
        {
            "id": "4",
            "text": "Neuralink's brain-computer interface showing promising results in latest trials. The future of human-AI symbiosis.",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T13:00:00Z",
            "public_metrics": {"like_count": 60000, "retweet_count": 12000, "reply_count": 2500, "view_count": 1500000},
            "url": "https://twitter.com/elonmusk/status/4",
            "is_retweet": False,
            "is_reply": False,
        },
        {
            "id": "5",
            "text": "Revenue projections for Q4 looking strong. Market efficiency improving.",
            "author_id": "elonmusk",
            "author_name": "Elon Musk",
            "created_at": "2025-11-22T14:00:00Z",
            "public_metrics": {"like_count": 40000, "retweet_count": 8000, "reply_count": 1500, "view_count": 1000000},
            "url": "https://twitter.com/elonmusk/status/5",
            "is_retweet": False,
            "is_reply": False,
        },
    ]


if __name__ == "__main__":
    asyncio.run(main())
