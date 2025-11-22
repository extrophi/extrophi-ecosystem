# Naval Ravikant Content Scraper

Specialized scraper for extracting Naval Ravikant's philosophy, economics, and wisdom content from Twitter and YouTube.

## Overview

The Naval scraper (`NavalScraper`) is a high-level scraper that combines Twitter and YouTube platform scrapers to collect Naval's content across multiple platforms. It adds Naval-specific intelligence including:

- Thread detection and unrolling
- Content type classification (philosophy, economics, technology, health, wisdom)
- Source tagging for attribution
- Comprehensive metrics and reporting

## Features

### Twitter Scraping (@naval)
- ✅ Scrapes tweets from @naval timeline
- ✅ Detects threads (1/, Thread:, 🧵)
- ✅ Extracts engagement metrics (likes, retweets, replies)
- ✅ Uses Playwright with anti-bot fingerprint spoofing (IAC-024 patterns)
- ✅ Human-like scrolling and rate limiting
- ✅ Supports up to 2,000 tweets per session

### YouTube Scraping
- ✅ Searches for "Naval Ravikant podcast" appearances
- ✅ Extracts full transcripts using youtube-transcript-api
- ✅ Captures video metadata (title, channel, views, likes, duration)
- ✅ Supports up to 50 videos per session
- ✅ Handles missing transcripts gracefully (falls back to description)

### Content Classification
Automatically categorizes content into:
- **Economics**: Wealth, business, investing, startups
- **Health**: Meditation, fitness, longevity, diet
- **Technology**: Coding, software, innovation
- **Philosophy**: Meaning, purpose, happiness, existential topics
- **Wisdom**: General life advice and aphorisms

## Installation

### Prerequisites
```bash
# Python 3.11+
python --version

# Install backend dependencies (using uv)
cd backend
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Dependencies
- `playwright>=1.40.0` - For Twitter scraping
- `youtube-transcript-api>=0.6.0` - For YouTube transcripts
- `yt-dlp>=2023.11.16` - For YouTube metadata
- FastAPI, Pydantic, SQLAlchemy (from backend)

## Usage

### Command Line

```bash
# Scrape both Twitter and YouTube (full corpus)
python scripts/scrape_naval.py --twitter-limit 2000 --youtube-limit 50

# Scrape only Twitter
python scripts/scrape_naval.py --platform twitter --limit 100

# Scrape only YouTube
python scripts/scrape_naval.py --platform youtube --limit 20

# Save results to JSON
python scripts/scrape_naval.py --platform all --output data/naval_corpus.json
```

### Python API

```python
import asyncio
from backend.scrapers.adapters.naval import NavalScraper

async def main():
    scraper = NavalScraper()

    # Health check
    health = await scraper.health_check()
    print(f"Status: {health['status']}")

    # Scrape full corpus
    results = await scraper.scrape_naval_corpus(
        twitter_limit=2000,
        youtube_limit=50
    )

    print(f"Tweets: {len(results['twitter'])}")
    print(f"Videos: {len(results['youtube'])}")
    print(f"Total: {results['total_items']}")
    print(f"Credits: {results['credits_used']:.2f}")

    # Top topics
    for topic, count in results['top_topics']:
        print(f"  {topic}: {count}")

asyncio.run(main())
```

### Using the Registry

```python
from backend.scrapers.registry import get_scraper

# Get Naval scraper from registry
scraper = get_scraper("naval")

# Extract Twitter content
tweets = await scraper.extract("twitter", limit=100)

# Extract YouTube content
videos = await scraper.extract("youtube", limit=20)

# Extract both
all_content = await scraper.extract("all", limit=50)
```

## Output Schema

### Twitter Output
```python
{
    "id": "1234567890",
    "text": "How to build wealth...",
    "author_id": "naval",
    "created_at": "2025-11-22T10:00:00Z",
    "public_metrics": {
        "like_count": 1000,
        "retweet_count": 200,
        "reply_count": 50
    },
    "source": "naval",
    "platform": "twitter",
    "is_thread": True
}
```

### YouTube Output
```python
{
    "video_id": "abc123xyz",
    "title": "Naval Ravikant on Joe Rogan Podcast",
    "transcript": "Full transcript text...",
    "segments": [...],  # Timestamped segments
    "duration": 7200,  # seconds
    "channel": "PowerfulJRE",
    "channel_id": "UCzQUP1qoWDoEbmsQxvdjxgQ",
    "view_count": 1000000,
    "like_count": 50000,
    "upload_date": "20251122",
    "source": "naval",
    "platform": "youtube"
}
```

### UnifiedContent Schema
After normalization:
```python
{
    "id": "uuid-string",
    "platform": "twitter",
    "source_url": "https://twitter.com/naval/status/123...",
    "author": {
        "id": "naval",
        "username": "naval",
        "platform": "twitter"
    },
    "content": {
        "title": None,
        "body": "Tweet text or transcript",
        "word_count": 42
    },
    "metrics": {
        "likes": 1000,
        "views": 5000,
        "comments": 50,
        "shares": 200
    },
    "metadata": {
        "source": "naval",
        "is_thread": True,
        "content_type": "economics"
    },
    "scraped_at": "2025-11-22T12:00:00Z"
}
```

## Testing

```bash
# Run Naval scraper tests
cd backend
pytest scrapers/tests/test_naval_scraper.py -v

# Run with coverage
pytest scrapers/tests/test_naval_scraper.py --cov=scrapers.adapters.naval

# Run all scraper tests
pytest scrapers/tests/ -v
```

## Performance

### Credits Budget
- **Twitter**: ~0.01 credits per tweet
  - 2,000 tweets = ~20 credits
- **YouTube**: ~1.0 credit per video (transcript extraction)
  - 50 videos = ~50 credits
- **Total**: ~70 credits for full corpus (well within 800 budget)

### Rate Limits
- Twitter: Human-like scrolling with 1-2 second delays
- YouTube: No API rate limits (uses public endpoints)
- Recommended: Run during off-peak hours to avoid detection

### Execution Time
- Twitter (2,000 tweets): ~15-20 minutes
- YouTube (50 videos): ~5-10 minutes
- Total: ~25-30 minutes for full corpus

## Architecture

```
NavalScraper
├── TwitterScraper (composition)
│   ├── Playwright browser automation
│   ├── Fingerprint spoofing (IAC-024)
│   ├── Human-like scrolling
│   └── Metric extraction
├── YouTubeScraper (composition)
│   ├── youtube-transcript-api
│   ├── yt-dlp for metadata
│   └── Multi-language support
└── Naval-specific logic
    ├── Thread detection
    ├── Content classification
    └── Topic analysis
```

## Known Limitations

1. **Twitter Authentication**: Currently uses unauthenticated scraping (public data only)
   - Can't access protected accounts
   - May hit rate limits on heavy usage
   - Consider adding OAuth for production

2. **YouTube Search**: Uses search results instead of curated playlists
   - May include non-Naval content if search is broad
   - Consider maintaining a curated playlist for best results

3. **Thread Unrolling**: Basic thread detection only
   - Doesn't automatically fetch thread continuations
   - Future: Add thread-unrolling logic

4. **Content Classification**: Keyword-based (not LLM)
   - Simple heuristics, not semantic analysis
   - Future: Add LLM-based classification

## Troubleshooting

### "Playwright not installed"
```bash
playwright install chromium
```

### "youtube-transcript-api not found"
```bash
uv pip install youtube-transcript-api yt-dlp
```

### Twitter scraping fails
- Check if @naval's profile is accessible
- Verify internet connection
- Twitter may be blocking automated access (rotate user agents)

### YouTube transcript unavailable
- Not all videos have transcripts
- Falls back to video description
- Check video language settings

## Future Enhancements

- [ ] Add thread unrolling (fetch full thread context)
- [ ] LLM-based content classification
- [ ] Support for Naval's podcast (search by show name)
- [ ] Export to knowledge graph format
- [ ] Integration with RAG/vector store
- [ ] Real-time monitoring (webhook on new Naval content)
- [ ] Deduplication (cross-platform content matching)

## Credits

Built using:
- IAC-024 Twitter OAuth patterns (fingerprint spoofing)
- IAC-032 Unified Scraper architecture (BaseScraper interface)
- IAC-033 Extrophi Ecosystem (monorepo integration)

## License

Part of the Extrophi Ecosystem. See root LICENSE file.
