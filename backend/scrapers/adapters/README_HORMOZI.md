# Hormozi Content Scraper

Multi-platform scraper for Alex Hormozi's business and marketing content.

## Features

- **YouTube Scraping**: @AlexHormozi channel videos, transcripts, and metadata
- **Twitter Scraping**: @AlexHormozi tweets, engagement metrics
- **Framework Detection**: Automatically identifies 20+ marketing frameworks
- **Theme Extraction**: Categorizes content (offer creation, sales, scaling, marketing)
- **Hook Analysis**: Detects content patterns (educational, mistake avoidance, insider knowledge)
- **Comprehensive Reporting**: JSON + Markdown exports with full insights

## Quick Start

```python
from backend.scrapers.adapters.hormozi import HormoziScraper

# Initialize
scraper = HormoziScraper()

# Health check
health = await scraper.health_check()

# Scrape content
report = await scraper.scrape_all(
    youtube_limit=50,
    twitter_limit=1000
)

# Access insights
print(f"Frameworks: {report['insights']['frameworks_identified']}")
print(f"Credits used: {report['summary']['credits_used']}")
```

## Registry Usage

```python
from backend.scrapers.registry import get_scraper

scraper = get_scraper("hormozi")
data = await scraper.extract(target="all", limit=20)
```

## CLI Testing

```bash
# Quick test (5 videos, 20 tweets)
python test_hormozi_scraper.py --mode quick

# Full scrape (50 videos, 1000 tweets)
python test_hormozi_scraper.py --mode full
```

## Marketing Frameworks Tracked

1. Value ladder
2. Grand slam offer
3. Lead magnet
4. Irresistible offer
5. Pricing strategy
6. Customer acquisition
7. LTV (Lifetime value)
8. Conversion rate
9. Sales script
10. Close rate
11. Objection handling
12. Scarcity & urgency
13. Guarantee & risk reversal
14. Value equation
15. Dream outcome
16. Perceived likelihood
17. Time delay
18. Effort & sacrifice
19. And more...

## Output Structure

### UnifiedContent Schema

```python
{
    "platform": "youtube" | "twitter",
    "source_url": "https://...",
    "author": {
        "id": "...",
        "username": "AlexHormozi",
        "platform": "..."
    },
    "content": {
        "title": "...",
        "body": "...",
        "word_count": 1234
    },
    "metrics": {
        "likes": 5000,
        "views": 100000,
        "engagement_rate": 5.0
    },
    "analysis": {
        "frameworks": ["value ladder", "grand slam offer"],
        "themes": ["offer_creation", "sales_process"],
        "hooks": ["educational_hook"],
        "keywords": [...]
    },
    "metadata": {
        "source": "hormozi",
        "author": "Alex Hormozi",
        "content_type": "business_marketing"
    }
}
```

### Report Output

**JSON** (`hormozi_report_{mode}_{timestamp}.json`):
- Full content data
- All metadata and metrics
- Platform breakdown
- Framework/theme/hook detection

**Markdown** (`hormozi_summary_{mode}_{timestamp}.md`):
- Executive summary
- Platform statistics
- Framework lists
- Engagement metrics

## Configuration

### Adjust Limits

```python
scraper = HormoziScraper()
scraper.max_credits = 2000  # Increase budget

report = await scraper.scrape_all(
    youtube_limit=100,  # More videos
    twitter_limit=2000  # More tweets
)
```

### Add Custom Frameworks

Edit `FRAMEWORKS` list in `hormozi.py`:

```python
FRAMEWORKS = [
    "value ladder",
    "grand slam offer",
    # Add custom:
    "tripwire offer",
    "upsell sequence",
]
```

## Architecture

```
HormoziScraper (orchestrator)
    ├── YouTubeScraper (yt-dlp + youtube-transcript-api)
    ├── TwitterScraper (Playwright + stealth mode)
    └── Framework/Theme/Hook analysis
```

## Dependencies

All included in `backend/pyproject.toml`:
- `playwright` - Twitter scraping
- `youtube-transcript-api` - YouTube transcripts
- `yt-dlp` - YouTube metadata
- `pydantic` - Data validation

## Performance

**YouTube**: ~5-10 seconds per video
**Twitter**: ~2-3 seconds per tweet

**Full Scrape** (50 videos + 1000 tweets):
- Time: ~45-60 minutes
- Memory: ~500MB peak
- Network: ~10MB data

## Limitations

1. **Network Access**: Requires unrestricted internet
2. **Rate Limiting**: Respects platform limits
3. **Framework Detection**: Keyword-based (not LLM in v1)
4. **Twitter Access**: May require cookies or auth for large scrapes

## Future Enhancements

- [ ] LLM-powered framework analysis (GPT-4)
- [ ] ChromaDB vector search integration
- [ ] FastAPI REST endpoints
- [ ] Real-time streaming mode
- [ ] Multi-creator support

## Documentation

- Full report: `docs/agents/hormozi-scraper-agent4-report.md`
- Code: `backend/scrapers/adapters/hormozi.py`
- Tests: `test_hormozi_scraper.py`

## Author

Agent #4 - Alex Hormozi Content Scraper
Branch: `claude/hormozi-content-scraper-01SnMybzRcUerNzL8MP39Bwx`
