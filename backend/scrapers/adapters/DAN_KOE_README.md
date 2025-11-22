# Dan Koe Content Scraper

Multi-platform content scraper for Dan Koe's YouTube, Twitter/X, and Substack content.

## Overview

The Dan Koe scraper is an orchestrator that coordinates three platform-specific scrapers to collect and store Dan Koe's content from:

1. **YouTube** (@thedankoe) - Video transcripts and metadata
2. **Twitter/X** (@thedankoe) - Tweets and engagement metrics
3. **Substack** (dankoe.substack.com) - Blog articles

## Features

- **Multi-platform orchestration** - Scrapes from 3 platforms in one command
- **Credit tracking** - Configurable budget with max 1,000 credits
- **Database persistence** - Saves to PostgreSQL with unified schema
- **Comprehensive reporting** - Detailed stats and error tracking
- **Platform-specific adapters** - Leverages existing scraper infrastructure

## Installation

The scraper is part of the unified backend and uses existing dependencies:

```bash
cd backend
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -r requirements.txt
```

## Usage

### CLI Command

```bash
# Scrape all platforms (default)
python scrape_dan_koe.py

# Scrape specific platform
python scrape_dan_koe.py --platform youtube
python scrape_dan_koe.py --platform twitter
python scrape_dan_koe.py --platform substack

# Set custom credit limit
python scrape_dan_koe.py --credits 500

# Test mode (5 items per platform)
python scrape_dan_koe.py --test
```

### Programmatic Usage

```python
from backend.scrapers.adapters.dan_koe import DanKoeScraper

# Initialize scraper
scraper = DanKoeScraper(max_credits=1000)

# Run health check
health = await scraper.health_check()

# Scrape and save all platforms
report = await scraper.scrape_and_save(target="all")

# Access statistics
print(f"Total scraped: {report['total_scraped']}")
print(f"Total saved: {report['total_saved']}")
print(f"Credits used: {report['credits_used']}")
```

## Architecture

### Class: `DanKoeScraper`

Inherits from `BaseScraper` and orchestrates three platform scrapers:

- `YouTubeScraper` - Handles YouTube channel scraping
- `TwitterScraper` - Handles Twitter profile scraping
- `WebScraper` - Handles Substack blog scraping

### Key Methods

#### `health_check() -> dict`
Verifies connectivity for all platform scrapers.

#### `extract(target: str, limit: int) -> List[dict]`
Extracts raw content from specified platforms.

**Args:**
- `target`: Platform to scrape ("all", "youtube", "twitter", "substack")
- `limit`: Override default limits (0 = use defaults)

**Returns:** List of raw content dictionaries

#### `normalize(raw_data: dict) -> UnifiedContent`
Normalizes platform-specific data to unified schema.

#### `scrape_and_save(target: str) -> Dict[str, Any]`
Main orchestration method that scrapes and persists to database.

**Returns:** Comprehensive report with statistics

## Credit System

Credit costs are designed to reflect API/resource usage:

| Platform | Cost per Item | Default Limit | Total Cost |
|----------|---------------|---------------|------------|
| YouTube  | 1 credit      | 100 videos    | 100        |
| Twitter  | 0.5 credits   | 1000 tweets   | 500        |
| Substack | 1 credit      | 50 articles   | 50         |

**Total default cost:** ~650 credits (well within 1,000 budget)

## Database Schema

Content is saved to the `contents` table with:

```sql
-- Core fields
id: UUID (primary key)
platform: "youtube" | "twitter" | "web"
source_url: TEXT (unique)
author_id: VARCHAR(255)
content_title: TEXT
content_body: TEXT

-- Metrics (JSONB)
metrics: {
  likes: int,
  views: int,
  comments: int,
  shares: int,
  engagement_rate: float
}

-- Metadata (JSONB)
extra_metadata: {
  video_id: str (YouTube),
  tweet_id: str (Twitter),
  domain: str (Web),
  ...
}

-- Timestamps
scraped_at: TIMESTAMP
published_at: TIMESTAMP
```

## Output Report

The scraper generates a comprehensive report:

```
Dan Koe Content Scraper Report
Generated: 2023-11-16T10:30:00Z

TOTALS:
  Total Items Scraped: 150
  Total Items Saved:   148
  Total Errors:        2
  Credits Used:        125.50 / 1000

PLATFORM BREAKDOWN:

YouTube (@thedankoe):
  Scraped: 100
  Saved:   99
  Errors:  1

Twitter (@thedankoe):
  Scraped: 50
  Saved:   49
  Errors:  1

Substack (dankoe.substack.com):
  Scraped: 0
  Saved:   0
  Errors:  0

ERROR DETAILS:
...
```

Report is saved to `dan_koe_scraper_report.txt`.

## Error Handling

The scraper implements comprehensive error handling:

1. **Platform-level errors** - Catches scraper failures, continues with other platforms
2. **Item-level errors** - Logs individual failures, continues scraping
3. **Credit limit enforcement** - Stops scraping when budget exhausted
4. **Duplicate detection** - Skips items already in database

All errors are logged to the report with details.

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_dan_koe_scraper.py -v
```

Test coverage includes:
- Health checks
- Platform-specific scraping
- Credit limit enforcement
- Data normalization
- Error handling
- Report generation

## Platform-Specific Notes

### YouTube
- Uses `youtube-transcript-api` for free transcript access
- Falls back to description if transcript unavailable
- Extracts metadata via `yt-dlp`

### Twitter/X
- Uses Playwright for stealth scraping
- Implements fingerprint spoofing (IAC-024 patterns)
- Adaptive rate limiting to avoid detection

### Substack
- Uses Jina.ai Reader API (free tier: 50K pages/month)
- Parses archive page for article URLs
- Converts to clean markdown

## Limitations

1. **Rate limits** - Twitter scraping may be slow due to anti-bot measures
2. **Transcript availability** - Some YouTube videos may not have transcripts
3. **Substack pagination** - Currently limited to visible archive links
4. **Credit accuracy** - Costs are estimates, actual usage may vary

## Future Enhancements

- [ ] Implement LLM analysis for content enrichment
- [ ] Add vector embeddings for semantic search
- [ ] Support incremental updates (only new content)
- [ ] Add pattern detection across platforms
- [ ] Implement webhook notifications for new content

## Related Files

- `backend/scrapers/adapters/dan_koe.py` - Main scraper class
- `backend/scrapers/adapters/youtube.py` - YouTube scraper
- `backend/scrapers/adapters/twitter.py` - Twitter scraper
- `backend/scrapers/adapters/web.py` - Web/Substack scraper
- `backend/scrapers/base.py` - Base scraper interface
- `backend/db/repository.py` - Database operations
- `backend/tests/test_dan_koe_scraper.py` - Test suite
- `scrape_dan_koe.py` - CLI script

## License

Part of the IAC-033 Extrophi Ecosystem monorepo.

## Author

Agent #2: Dan Koe Content Scraper
Created: 2025-11-22
