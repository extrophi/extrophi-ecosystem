# Daniel Throssell Scraper - Agent #5 Documentation

## Overview

The **Daniel Throssell Scraper** is a specialized content intelligence tool designed to extract copywriting expertise from Daniel Throssell's online presence. It combines Twitter scraping and web scraping to gather comprehensive copywriting insights, email marketing strategies, and persuasion frameworks.

## Target Sources

### 1. Twitter (@danielthrossell)
- **Limit**: 2,000 tweets (configurable)
- **Focus**:
  - Email marketing insights
  - Copywriting tips and techniques
  - Storytelling patterns
  - Hook formulas
  - Persuasion frameworks

### 2. Websites
- **Primary**: https://persuasivepage.com/
  - Main teaching platform
  - Email Copywriting Compendium
  - CopyMart products
- **Secondary**: https://danielthrossell.com/
  - Personal site
  - Additional resources

## Features

### Multi-Source Scraping
- **Twitter Integration**: Uses advanced Playwright-based scraper with:
  - Fingerprint spoofing (canvas, WebGL, audio)
  - Human-like behavior simulation
  - Adaptive rate limiting
  - Session persistence

- **Web Integration**: Leverages Jina.ai Reader API:
  - 50,000 pages/month FREE tier
  - Automatic markdown conversion
  - Clean content extraction

### Copywriting Analysis
- **High-engagement detection**: Identifies tweets with 50+ likes/shares
- **Keyword frequency analysis**: Tracks copywriting-specific terms
- **Framework detection**: Identifies mentions of AIDA, PAS, PASTOR, etc.
- **Metrics tracking**: Word count, engagement rates, content patterns

### Unified Data Model
All content is normalized to the `UnifiedContent` schema:
- **source**: "throssell"
- **platform**: "twitter" or "website"
- **Rich metadata**: Specialization, focus areas, author info
- **Metrics**: Likes, shares, comments, engagement rates

## Installation

### Prerequisites
```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r backend/requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Dependencies
- `pydantic>=2.5.0` - Data validation
- `playwright>=1.40.0` - Twitter scraping
- `httpx>=0.25.0` - Web scraping

## Usage

### Quick Start

```bash
# Run test mode (20 tweets)
python test_throssell_scraper.py --mode test

# Run small scrape (100 tweets)
python test_throssell_scraper.py --mode small

# Run medium scrape (500 tweets)
python test_throssell_scraper.py --mode medium

# Run full scrape (2000 tweets)
python test_throssell_scraper.py --mode full

# Custom limit
python test_throssell_scraper.py --tweet-limit 250

# Custom output file
python test_throssell_scraper.py --mode small --output my_results.json
```

### Programmatic Usage

```python
import asyncio
from backend.scrapers.adapters.throssell import ThrossellScraper

async def scrape_throssell():
    # Initialize scraper
    scraper = ThrossellScraper()

    # Health check
    health = await scraper.health_check()
    print(f"Status: {health['status']}")

    # Run full scrape
    report = await scraper.scrape_all(tweet_limit=2000)

    # Access results
    print(f"Total items: {report['statistics']['total_items']}")
    print(f"Tweets: {report['statistics']['tweets_scraped']}")
    print(f"Web pages: {report['statistics']['web_pages_scraped']}")
    print(f"Credits used: {report['statistics']['credits_used']}")

    # Access content
    for item in report['content'][:10]:
        print(f"[{item.platform}] {item.content.body[:100]}...")

asyncio.run(scrape_throssell())
```

### Using the Scraper Registry

```python
from backend.scrapers.registry import get_scraper

# Get Throssell scraper via registry
scraper = get_scraper("throssell")

# Extract data
raw_data = await scraper.extract("all", limit=100)

# Normalize data
normalized = [await scraper.normalize(item) for item in raw_data]
```

## Output Format

### JSON Structure

```json
{
  "agent": "Agent #5: Daniel Throssell Scraper",
  "timestamp": "2025-11-22T10:30:00.000000",
  "statistics": {
    "total_items": 2004,
    "tweets_scraped": 2000,
    "web_pages_scraped": 4,
    "total_words": 45678,
    "credits_used": 1004.0,
    "credits_remaining": -204.0
  },
  "copywriting_insights": {
    "high_engagement_count": 245,
    "avg_tweet_length": 18.5,
    "copywriting_keyword_frequency": {
      "email": 523,
      "copywriting": 312,
      "persuasion": 89,
      "hook": 156,
      "framework": 45
    },
    "potential_frameworks_mentioned": 45
  },
  "content": [
    {
      "content_id": "uuid-here",
      "platform": "twitter",
      "source_url": "https://twitter.com/danielthrossell/status/123...",
      "author": {
        "id": "danielthrossell",
        "platform": "twitter",
        "username": "danielthrossell",
        "display_name": null
      },
      "content": {
        "title": null,
        "body": "Tweet text here...",
        "word_count": 18
      },
      "metrics": {
        "likes": 142,
        "views": 0,
        "comments": 8,
        "shares": 23,
        "engagement_rate": 0.0
      },
      "metadata": {
        "tweet_id": "123456789",
        "created_at": "2025-11-20T15:30:00Z",
        "source": "throssell",
        "author_name": "Daniel Throssell",
        "specialization": "email_copywriting",
        "focus_areas": [
          "copywriting_techniques",
          "email_marketing",
          "persuasion_frameworks",
          "storytelling",
          "hook_formulas"
        ]
      },
      "scraped_at": "2025-11-22T10:30:00.000000"
    }
  ]
}
```

## Credit Usage

### Budget: 800 Credits Maximum

**Breakdown**:
- **Twitter**: ~0.5 credits per tweet (Playwright scraping)
  - 2,000 tweets = 1,000 credits ⚠️ **EXCEEDS BUDGET**
  - Recommended: 1,600 tweets max (800 credits)

- **Jina.ai Web Scraping**: FREE (50,000 pages/month)
  - persuasivepage.com: 0 credits
  - danielthrossell.com: 0 credits
  - Blog paths: 0 credits

**Optimization Strategies**:
1. **Reduce tweet limit**: `--tweet-limit 1600` (stays within budget)
2. **Twitter-only scrape**: Skip websites if needed
3. **Website-only scrape**: Skip Twitter for zero credits
4. **Batch processing**: Scrape in multiple sessions

### Example Budget-Conscious Runs

```bash
# Stay within 800 credit budget (Twitter + Web)
python test_throssell_scraper.py --tweet-limit 1600

# Twitter only (exactly 800 credits)
python test_throssell_scraper.py --tweet-limit 1600

# Websites only (0 credits)
# (requires code modification to target="website")
```

## File Structure

```
backend/scrapers/adapters/
├── throssell.py          # Main scraper implementation
├── twitter.py            # Twitter scraper (dependency)
└── web.py                # Web scraper (dependency)

backend/scrapers/
├── base.py               # BaseScraper interface
├── registry.py           # Scraper registry (updated)
└── __init__.py

test_throssell_scraper.py # Test/execution script
THROSSELL_SCRAPER_DOCUMENTATION.md  # This file
```

## Architecture

### Class: `ThrossellScraper`

**Inherits**: `BaseScraper`

**Key Methods**:

1. **`health_check()`**
   - Verifies Twitter and Web scrapers are operational
   - Returns status dict with component health

2. **`extract(target, limit)`**
   - Extracts raw content from Twitter and/or websites
   - `target`: "all", "twitter", "website", or specific URL
   - `limit`: Max tweets to fetch (default 2000)

3. **`normalize(raw_data)`**
   - Converts raw data to UnifiedContent schema
   - Adds Throssell-specific metadata
   - Delegates to appropriate scraper (Twitter/Web)

4. **`scrape_all(tweet_limit)`**
   - Complete workflow: extract → normalize → analyze
   - Returns comprehensive report with statistics

5. **`_scrape_websites()`**
   - Internal method to scrape all target websites
   - Handles errors gracefully

6. **`_analyze_copywriting_patterns(content)`**
   - Analyzes copywriting-specific patterns
   - Identifies high-engagement content
   - Tracks keyword frequency

### Data Flow

```
Input: tweet_limit (default 2000)
  ↓
extract() → Scrape Twitter + Websites
  ↓
Raw Data (list[dict])
  ↓
normalize() → Convert to UnifiedContent
  ↓
Normalized Data (list[UnifiedContent])
  ↓
_analyze_copywriting_patterns() → Extract insights
  ↓
Report (dict) with statistics + content
```

## Copywriting Focus Areas

The scraper is optimized to extract:

### 1. Email Marketing Insights
- Subject line formulas
- Email structure patterns
- Call-to-action strategies
- Engagement techniques

### 2. Copywriting Techniques
- Hook formulas
- Storytelling patterns
- Curiosity generation
- Specificity principles

### 3. Persuasion Frameworks
- AIDA (Attention, Interest, Desire, Action)
- PAS (Problem, Agitate, Solution)
- PASTOR (Problem, Amplify, Story, Transformation, Offer, Response)
- BAB (Before, After, Bridge)

### 4. Voice of Customer (VOC)
- Pain point articulation
- Desire identification
- Objection handling
- Emotional triggers

## Integration with Research Pipeline

### Storage
The scraper outputs can be integrated with:
- **PostgreSQL**: Store in `contents` table
- **ChromaDB**: Generate embeddings for semantic search
- **LLM Analysis**: GPT-4 for framework extraction

### Example Integration

```python
from backend.scrapers.adapters.throssell import ThrossellScraper
from backend.db.repository import ContentRepository
from backend.vector.embeddings import generate_embeddings

# Scrape
scraper = ThrossellScraper()
report = await scraper.scrape_all(tweet_limit=1600)

# Store in database
repo = ContentRepository()
for item in report['content']:
    # Generate embedding
    embedding = generate_embeddings(item.content.body)
    item.embedding = embedding

    # Save to PostgreSQL
    await repo.create(item)

# Now queryable via RAG
results = await repo.semantic_search("email copywriting hooks")
```

## Known Limitations

### Network Constraints
- **Twitter rate limiting**: Twitter may block aggressive scraping
- **Anti-bot detection**: Uses fingerprint spoofing, but not foolproof
- **Network errors**: Requires retry logic (included in TwitterScraper)

### Budget Constraints
- **2,000 tweet limit exceeds budget**: Reduce to 1,600 or less
- **Free tier dependency**: Jina.ai has 50K page/month limit

### Content Constraints
- **Public content only**: No access to private tweets or paywalled content
- **Temporal limitation**: Only recent tweets (Twitter API constraint)
- **Dynamic content**: Some website content may require JavaScript rendering

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'pydantic'`
```bash
pip install pydantic httpx playwright
playwright install chromium
```

### Error: `ERR_TUNNEL_CONNECTION_FAILED`
- Network connectivity issue
- Check firewall/proxy settings
- Verify internet access

### Error: `No scraper registered for platform 'throssell'`
- Ensure `backend/scrapers/registry.py` includes Throssell auto-registration
- Check import statements

### Low Credit Warning
```
Credits remaining: -204.0
```
- Reduce `--tweet-limit` to stay within 800 budget
- Recommended: 1,600 tweets max

## Performance

### Expected Runtimes

| Mode   | Tweets | Web Pages | Estimated Time | Credits |
|--------|--------|-----------|----------------|---------|
| test   | 20     | 4         | 1-2 min        | 10      |
| small  | 100    | 4         | 5-8 min        | 50      |
| medium | 500    | 4         | 20-30 min      | 250     |
| full   | 2000   | 4         | 60-90 min      | 1000    |

**Budget-Safe**:
- **1,600 tweets**: ~50-70 min, 800 credits ✅

### Rate Limiting
- **Twitter**: Human-like delays (500-1500ms between requests)
- **Web**: No rate limits (Jina.ai free tier)

## Contributing

To extend the Throssell scraper:

1. **Add new websites**: Update `WEBSITES` or `BLOG_PATHS` lists
2. **Add analysis methods**: Extend `_analyze_copywriting_patterns()`
3. **Custom filtering**: Add filters in `extract()` method
4. **Enhanced metadata**: Modify `normalize()` to add custom fields

## References

### Daniel Throssell Resources
- **Twitter**: [@danielthrossell](https://twitter.com/danielthrossell)
- **Website**: [persuasivepage.com](https://persuasivepage.com/)
- **Personal Site**: [danielthrossell.com](https://danielthrossell.com/)
- **Email Compendium**: [persuasivepage.com/compendium/](https://persuasivepage.com/compendium/)

### Related Documentation
- [IAC-032 Unified Scraper](research/CLAUDE.md)
- [BaseScraper Interface](backend/scrapers/base.py)
- [Scraper Registry](backend/scrapers/registry.py)

## License

Part of the IAC-033 Extrophi Ecosystem monorepo.

---

**Agent**: #5 - Daniel Throssell Content Scraper
**Version**: 1.0
**Created**: 2025-11-22
**Author**: Claude Code (Anthropic)
