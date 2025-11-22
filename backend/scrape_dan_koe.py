#!/usr/bin/env python3
"""
Dan Koe Content Scraper CLI

Scrapes content from Dan Koe's YouTube, Twitter, and Substack.
Saves all content to the unified PostgreSQL database.

Usage:
    # Scrape all platforms
    python scrape_dan_koe.py

    # Scrape specific platform
    python scrape_dan_koe.py --platform youtube
    python scrape_dan_koe.py --platform twitter
    python scrape_dan_koe.py --platform substack

    # Set custom credit limit
    python scrape_dan_koe.py --credits 500

    # Test with limited data
    python scrape_dan_koe.py --test
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scrapers.adapters.dan_koe import DanKoeScraper


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape Dan Koe content from YouTube, Twitter, and Substack"
    )
    parser.add_argument(
        "--platform",
        choices=["all", "youtube", "twitter", "substack"],
        default="all",
        help="Platform to scrape (default: all)",
    )
    parser.add_argument(
        "--credits",
        type=int,
        default=1000,
        help="Maximum credits to use (default: 1000)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: scrape only 5 items per platform",
    )

    args = parser.parse_args()

    # Initialize scraper
    scraper = DanKoeScraper(max_credits=args.credits)

    # Run health check
    print("🏥 Running health check...")
    health = await scraper.health_check()
    print(f"Status: {health['status']}")

    if health["status"] != "ok":
        print("\n⚠️  Warning: Some scrapers are not fully operational")
        for platform, status in health["scrapers"].items():
            print(f"  {platform}: {status['status']} - {status['message']}")
        print()

    # Override limits for test mode
    if args.test:
        scraper.YOUTUBE_LIMIT = 5
        scraper.TWITTER_LIMIT = 5
        scraper.SUBSTACK_LIMIT = 5
        print("🧪 Test mode: Limited to 5 items per platform\n")

    # Run scraper
    try:
        report = await scraper.scrape_and_save(target=args.platform)

        # Save report to file
        report_file = Path("dan_koe_scraper_report.txt")
        report_file.write_text(report["summary"])
        print(f"📄 Report saved to: {report_file.absolute()}")

        # Exit with error code if there were errors
        if report["total_errors"] > 0:
            sys.exit(1)
        else:
            print("\n✅ Scraping completed successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
