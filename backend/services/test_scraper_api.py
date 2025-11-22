"""Test script for ScraperAPI integration."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scraper_api_service import (
    ScraperAPIConfig,
    ScraperAPIService,
    ScraperAPIRateLimitExceeded,
)


async def test_scraper_api():
    """Test ScraperAPI with a simple URL scrape."""
    # Get API key from environment
    api_key = os.getenv("SCRAPERAPI_KEY")
    if not api_key:
        print("ERROR: SCRAPERAPI_KEY environment variable not set")
        print("Set it with: export SCRAPERAPI_KEY='your_key_here'")
        return

    print("=" * 80)
    print("ScraperAPI Integration Test")
    print("=" * 80)

    # Create service with config
    config = ScraperAPIConfig(
        api_key=api_key,
        max_credits=4800,
        max_retries=3,
        initial_backoff=1.0,
    )

    service = ScraperAPIService(config)

    # Test URL (httpbin.org is great for testing)
    test_url = "http://httpbin.org/html"

    print(f"\nTest URL: {test_url}")
    print(f"Max credits: {config.max_credits}")
    print(f"Max retries: {config.max_retries}\n")

    try:
        # Get stats before scraping
        stats_before = await service.get_stats()
        print("Stats before scraping:")
        print(f"  Total credits used: {stats_before['total_credits_used']}")
        print(f"  Credits remaining: {stats_before['credits_remaining']}")
        print(f"  Percentage used: {stats_before['percentage_used']:.2f}%\n")

        # Perform scrape
        print("Scraping...")
        result = await service.scrape(test_url)

        print("\n✅ Scrape successful!")
        print(f"  URL: {result['url']}")
        print(f"  Status code: {result['status_code']}")
        print(f"  Credits used: {result['credits_used']}")
        print(f"  Elapsed time: {result['elapsed_time']:.2f}s")
        print(f"  Content length: {len(result['content'])} chars")
        print(f"  Content preview: {result['content'][:200]}...")

        # Get stats after scraping
        stats_after = await service.get_stats()
        print("\nStats after scraping:")
        print(f"  Total credits used: {stats_after['total_credits_used']}")
        print(f"  Credits remaining: {stats_after['credits_remaining']}")
        print(f"  Percentage used: {stats_after['percentage_used']:.2f}%")

        print("\n" + "=" * 80)
        print("Test completed successfully! ✅")
        print("=" * 80)

    except ScraperAPIRateLimitExceeded as e:
        print(f"\n❌ Rate limit exceeded: {e}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_scraper_api())
