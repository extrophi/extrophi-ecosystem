# AGENT EPSILON: Web/Jina Scraper Implementation

## MISSION: Scrape Blog Articles and Web Content with FREE Tier Priority

**Agent ID**: Epsilon
**Role**: Web/Blog Platform Adapter
**Priority**: HIGH (Scrapes thought leader blogs, documentation, articles)
**Estimated Time**: 2-3 hours

---

## EXECUTIVE SUMMARY

Build a web scraper that extracts content from blogs, articles, and documentation using a cost-optimized dual strategy:

1. **Primary**: Jina.ai Reader API (50,000 pages/month FREE - NO credit card required)
2. **Fallback**: ScraperAPI ($49/mo only when FREE tier exhausted or JS-rendering needed)

**Key Insight**: 80% of blog content is static HTML. Jina.ai converts this to clean markdown for FREE. Only use ScraperAPI for:
- JavaScript-rendered pages (SPAs, dynamic content)
- Anti-bot protected sites
- When Jina.ai fails

**Cost Savings**: $0/month for static content vs. $49/month baseline. Scale to $49/mo only if you exceed 50K pages or need JS rendering.

---

## JINA.AI READER API OVERVIEW

**Endpoint**: `https://r.jina.ai/{URL}`

**Features** (FREE tier):
- 50,000 pages/month
- Automatic HTML to Markdown conversion
- Handles complex layouts (headers, lists, code blocks)
- No authentication required
- No API key needed for basic usage
- LLM-optimized output

**Example**:
```bash
# Simple GET request - returns markdown
curl https://r.jina.ai/https://dankoe.com/blog/

# With headers for better control
curl -H "Accept: text/markdown" \
     https://r.jina.ai/https://dankoe.com/blog/
```

---

## DEPENDENCIES TO ADD

### Update `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...

    # Web Scraping
    "httpx>=0.25.0",         # Modern async HTTP client
    "beautifulsoup4>=4.12.0", # HTML parsing fallback
    "markdownify>=0.11.0",    # HTML to Markdown conversion
    "lxml>=4.9.0",            # Fast HTML parser

    # ScraperAPI Fallback (only for JS-rendered pages)
    "requests>=2.31.0",

    # Content Analysis
    "readability-lxml>=0.8.1", # Extract article content
    "trafilatura>=1.6.0",      # Web content extraction
]
```

---

## FILES TO CREATE

### Directory Structure
```
backend/
  scrapers/
    adapters/
      web.py                       # WebScraper (main adapter)
      _jina_client.py              # Primary: Jina.ai Reader API
      _scraperapi_client.py        # Fallback: ScraperAPI for JS rendering
      _content_extractor.py        # Article/content extraction utilities
```

---

## STEP 1: Create Jina.ai Reader Client (Primary - FREE)

### File: `backend/scrapers/adapters/_jina_client.py`

```python
"""
Jina.ai Reader API Client
Primary web scraper: FREE tier with 50K pages/month
Converts web pages to clean, LLM-ready markdown
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote_plus

import httpx


class JinaReaderClient:
    """
    Jina.ai Reader API wrapper

    FREE Tier Limits:
    - 50,000 pages/month
    - No API key required for basic usage
    - Rate limit: 200 req/min (generous)

    Features:
    - Automatic HTML to Markdown conversion
    - Preserves formatting (headers, lists, code)
    - Removes ads, navigation, clutter
    - LLM-optimized output
    """

    BASE_URL = "https://r.jina.ai"

    def __init__(self):
        """Initialize Jina Reader client"""
        # Async HTTP client with generous timeouts
        self.client = httpx.AsyncClient(
            timeout=60.0,  # Web pages can be slow
            follow_redirects=True,
            headers={
                "User-Agent": "IAC-032-UnifiedScraper/1.0",
                "Accept": "text/markdown"
            }
        )

        # Rate limiting (self-imposed)
        self.requests_made_today = 0
        self.requests_made_month = 0
        self.day_start = datetime.utcnow().date()
        self.month_start = datetime.utcnow().replace(day=1).date()
        self.last_request_time = datetime.utcnow()

        # Limits
        self.monthly_limit = 50000  # FREE tier
        self.daily_soft_limit = 1667  # ~50K/30 days
        self.min_interval_ms = 300  # 200 req/min = 300ms between

        # Error tracking
        self.error_count = 0
        self.consecutive_errors = 0

    def _check_limits(self):
        """Check rate limits before request"""
        now = datetime.utcnow()

        # Reset daily counter
        if now.date() != self.day_start:
            self.requests_made_today = 0
            self.day_start = now.date()

        # Reset monthly counter
        if now.replace(day=1).date() != self.month_start:
            self.requests_made_month = 0
            self.month_start = now.replace(day=1).date()

        # Check monthly limit
        if self.requests_made_month >= self.monthly_limit:
            raise Exception(
                f"Monthly FREE tier limit reached ({self.monthly_limit} pages). "
                "Use ScraperAPI fallback or wait for reset."
            )

        # Warn if approaching limit
        if self.requests_made_month > self.monthly_limit * 0.9:
            print(
                f"WARNING: Approaching Jina.ai monthly limit "
                f"({self.requests_made_month}/{self.monthly_limit})"
            )

    async def _respect_rate_limit(self):
        """Ensure we respect rate limits"""
        elapsed_ms = (
            datetime.utcnow() - self.last_request_time
        ).total_seconds() * 1000

        if elapsed_ms < self.min_interval_ms:
            wait_ms = self.min_interval_ms - elapsed_ms
            await asyncio.sleep(wait_ms / 1000)

        self.last_request_time = datetime.utcnow()

    async def fetch_as_markdown(self, url: str) -> Optional[dict]:
        """
        Fetch web page and convert to markdown using Jina.ai Reader

        Args:
            url: Web page URL to fetch

        Returns:
            dict: {
                'url': str,              # Original URL
                'markdown': str,         # Converted markdown content
                'title': str,            # Page title (if detected)
                'word_count': int,       # Content word count
                'char_count': int,       # Content character count
                'fetch_time': datetime,  # When fetched
                'source': 'jina'         # Indicates Jina.ai was used
            }
        """
        self._check_limits()
        await self._respect_rate_limit()

        # Encode URL for Jina.ai endpoint
        jina_url = f"{self.BASE_URL}/{url}"

        try:
            response = await self.client.get(jina_url)
            response.raise_for_status()

            markdown_content = response.text

            # Extract title from first markdown header
            title = self._extract_title(markdown_content)

            # Update counters
            self.requests_made_today += 1
            self.requests_made_month += 1
            self.consecutive_errors = 0

            return {
                'url': url,
                'markdown': markdown_content,
                'title': title,
                'word_count': len(markdown_content.split()),
                'char_count': len(markdown_content),
                'fetch_time': datetime.utcnow(),
                'source': 'jina'
            }

        except httpx.HTTPStatusError as e:
            self.error_count += 1
            self.consecutive_errors += 1

            if e.response.status_code == 402:
                # Payment required - FREE tier exhausted
                print(f"Jina.ai FREE tier exhausted. Use ScraperAPI fallback.")
                return None
            elif e.response.status_code == 429:
                # Rate limited
                print(f"Jina.ai rate limited. Waiting...")
                await asyncio.sleep(60)
                return await self.fetch_as_markdown(url)
            else:
                print(f"Jina.ai error for {url}: {e.response.status_code}")
                return None

        except httpx.RequestError as e:
            self.error_count += 1
            self.consecutive_errors += 1
            print(f"Network error fetching {url}: {e}")
            return None

        except Exception as e:
            self.error_count += 1
            self.consecutive_errors += 1
            print(f"Unexpected error for {url}: {e}")
            return None

    def _extract_title(self, markdown: str) -> str:
        """Extract title from markdown content"""
        lines = markdown.strip().split('\n')

        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()

        return "Untitled"

    async def fetch_multiple(self, urls: list[str]) -> list[dict]:
        """
        Fetch multiple URLs with rate limiting

        Args:
            urls: List of URLs to fetch

        Returns:
            list[dict]: Results for each URL (None for failures)
        """
        results = []

        for i, url in enumerate(urls):
            print(f"Fetching {i+1}/{len(urls)}: {url[:60]}...")
            result = await self.fetch_as_markdown(url)
            results.append(result)

            # Small delay between requests
            if i < len(urls) - 1:
                await asyncio.sleep(0.5)

        return results

    def get_usage_stats(self) -> dict:
        """Get current usage statistics"""
        return {
            'requests_today': self.requests_made_today,
            'requests_month': self.requests_made_month,
            'monthly_limit': self.monthly_limit,
            'monthly_remaining': self.monthly_limit - self.requests_made_month,
            'daily_soft_limit': self.daily_soft_limit,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup"""
        # Note: Can't await in __del__, client will be garbage collected
        pass


# Convenience function
async def fetch_with_jina(url: str) -> Optional[dict]:
    """Quick fetch using Jina.ai Reader"""
    client = JinaReaderClient()
    result = await client.fetch_as_markdown(url)
    await client.close()
    return result


if __name__ == "__main__":
    # Test Jina.ai Reader
    async def test():
        client = JinaReaderClient()

        # Test with a blog post
        url = "https://dankoe.com/blog/"
        print(f"Fetching {url} with Jina.ai Reader...")

        result = await client.fetch_as_markdown(url)

        if result:
            print(f"Title: {result['title']}")
            print(f"Word count: {result['word_count']}")
            print(f"Source: {result['source']}")
            print(f"\nContent preview:\n{result['markdown'][:500]}...")
        else:
            print("Failed to fetch")

        print(f"\nUsage stats: {client.get_usage_stats()}")
        await client.close()

    asyncio.run(test())
```

---

## STEP 2: Create ScraperAPI Fallback Client

### File: `backend/scrapers/adapters/_scraperapi_client.py`

```python
"""
ScraperAPI Client
Fallback scraper for JS-rendered pages and anti-bot protected sites
PAID: $49/month for 100K credits (only use when Jina.ai fails)
"""

import os
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
import markdownify


class ScraperAPIClient:
    """
    ScraperAPI wrapper for complex web scraping

    Pricing ($49/mo Hobby Plan):
    - Simple page: 1 credit ($0.00049)
    - JS-rendered: +5 credits
    - Residential proxy: +25 credits
    - 100K credits/month included

    Use ONLY when Jina.ai fails:
    - JavaScript-rendered pages (SPAs, React apps)
    - Anti-bot protected sites
    - Sites that block Jina.ai

    IMPORTANT: This costs money. Jina.ai is FREE.
    """

    BASE_URL = "https://api.scraperapi.com"

    def __init__(self):
        """Initialize ScraperAPI client"""
        self.api_key = os.getenv("SCRAPER_API_KEY")

        if not self.api_key:
            print(
                "WARNING: SCRAPER_API_KEY not set. "
                "ScraperAPI fallback will not work."
            )

        # Track usage
        self.credits_used = 0
        self.requests_made = 0
        self.last_request_time = datetime.utcnow()
        self.error_count = 0

    def fetch_page(
        self,
        url: str,
        render_js: bool = False,
        use_residential: bool = False
    ) -> Optional[dict]:
        """
        Fetch web page using ScraperAPI

        Args:
            url: URL to fetch
            render_js: Enable JavaScript rendering (+5 credits)
            use_residential: Use residential proxy (+25 credits)

        Returns:
            dict: {
                'url': str,
                'html': str,
                'markdown': str,
                'title': str,
                'word_count': int,
                'char_count': int,
                'credits_used': int,
                'fetch_time': datetime,
                'source': 'scraperapi'
            }
        """
        if not self.api_key:
            raise ValueError("SCRAPER_API_KEY not configured")

        # Calculate credits
        credits = 1
        if render_js:
            credits += 5
        if use_residential:
            credits += 25

        params = {
            "api_key": self.api_key,
            "url": url,
            "render": str(render_js).lower()
        }

        if use_residential:
            params["premium"] = "true"

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=60
            )
            response.raise_for_status()

            html_content = response.text

            # Convert HTML to markdown
            soup = BeautifulSoup(html_content, 'lxml')

            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Remove scripts, styles, navigation
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Convert to markdown
            markdown_content = markdownify.markdownify(
                str(soup),
                heading_style="ATX",
                strip=['a']  # Remove links for cleaner text
            )

            # Clean up markdown
            markdown_content = self._clean_markdown(markdown_content)

            # Update tracking
            self.credits_used += credits
            self.requests_made += 1
            self.last_request_time = datetime.utcnow()

            return {
                'url': url,
                'html': html_content,
                'markdown': markdown_content,
                'title': title,
                'word_count': len(markdown_content.split()),
                'char_count': len(markdown_content),
                'credits_used': credits,
                'fetch_time': datetime.utcnow(),
                'source': 'scraperapi'
            }

        except requests.exceptions.HTTPError as e:
            self.error_count += 1
            if e.response.status_code == 401:
                print("ScraperAPI: Invalid API key")
            elif e.response.status_code == 403:
                print(f"ScraperAPI: Forbidden - check account status")
            elif e.response.status_code == 429:
                print("ScraperAPI: Rate limited")
            else:
                print(f"ScraperAPI HTTP error: {e.response.status_code}")
            return None

        except Exception as e:
            self.error_count += 1
            print(f"ScraperAPI error for {url}: {e}")
            return None

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown output"""
        lines = markdown.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove excessive whitespace
            line = line.strip()

            # Skip empty lines (but keep some for structure)
            if not line and cleaned_lines and cleaned_lines[-1] == '':
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def get_usage_stats(self) -> dict:
        """Get usage statistics"""
        return {
            'credits_used': self.credits_used,
            'requests_made': self.requests_made,
            'error_count': self.error_count,
            'last_request': self.last_request_time.isoformat(),
            'api_key_configured': bool(self.api_key)
        }


# Convenience function
def fetch_with_scraperapi(url: str, render_js: bool = True) -> Optional[dict]:
    """Quick fetch using ScraperAPI"""
    client = ScraperAPIClient()
    return client.fetch_page(url, render_js=render_js)


if __name__ == "__main__":
    # Test ScraperAPI (requires API key)
    client = ScraperAPIClient()

    if client.api_key:
        url = "https://example.com"
        print(f"Fetching {url} with ScraperAPI...")

        result = client.fetch_page(url, render_js=False)

        if result:
            print(f"Title: {result['title']}")
            print(f"Word count: {result['word_count']}")
            print(f"Credits used: {result['credits_used']}")
            print(f"\nContent preview:\n{result['markdown'][:500]}...")
        else:
            print("Failed to fetch")

        print(f"\nUsage stats: {client.get_usage_stats()}")
    else:
        print("SCRAPER_API_KEY not set. Skipping test.")
```

---

## STEP 3: Create Content Extraction Utilities

### File: `backend/scrapers/adapters/_content_extractor.py`

```python
"""
Web Content Extraction Utilities
Extract metadata, clean content, and identify article structure
"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    return domain


def extract_author_from_url(url: str) -> str:
    """
    Attempt to extract author/site name from URL

    Examples:
    - https://dankoe.com/blog/ -> "dankoe"
    - https://jamesclear.com/article -> "jamesclear"
    - https://medium.com/@author/post -> "author"
    """
    domain = extract_domain(url)

    # Handle Medium specially
    if 'medium.com' in domain:
        # Try to extract username from path
        path = urlparse(url).path
        if path.startswith('/@'):
            username = path.split('/')[1].replace('@', '')
            return username

    # For personal domains, use the domain name
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        return domain_parts[0]

    return domain


def extract_publish_date(markdown: str) -> Optional[datetime]:
    """
    Attempt to extract publication date from content

    Args:
        markdown: Markdown content

    Returns:
        datetime: Extracted date or None
    """
    # Common date patterns in content
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD-MM-YYYY
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',     # YYYY-MM-DD
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})',  # Month DD, YYYY
        r'(\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4})',    # DD Month YYYY
    ]

    text = markdown[:2000]  # Check first part of content

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Try to parse
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%B %d, %Y', '%d %B %Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

    return None


def clean_markdown_content(markdown: str) -> str:
    """
    Clean and normalize markdown content

    Args:
        markdown: Raw markdown text

    Returns:
        str: Cleaned markdown
    """
    # Remove multiple consecutive blank lines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Remove image references (keep alt text)
    markdown = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', markdown)

    # Remove empty links
    markdown = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', markdown)

    # Normalize headers (ensure space after #)
    markdown = re.sub(r'^(#+)([^\s#])', r'\1 \2', markdown, flags=re.MULTILINE)

    # Remove excessive whitespace
    lines = []
    for line in markdown.split('\n'):
        line = line.rstrip()
        lines.append(line)

    markdown = '\n'.join(lines)

    return markdown.strip()


def extract_article_metadata(markdown: str, url: str) -> dict:
    """
    Extract metadata from article markdown

    Args:
        markdown: Article content in markdown
        url: Original URL

    Returns:
        dict: Metadata including title, author, date, etc.
    """
    # Extract title from first header
    title = "Untitled"
    lines = markdown.strip().split('\n')
    for line in lines[:15]:
        if line.startswith('# '):
            title = line[2:].strip()
            break
        elif line.startswith('## '):
            title = line[3:].strip()
            break

    # Extract author from URL
    author = extract_author_from_url(url)

    # Extract publication date
    pub_date = extract_publish_date(markdown)

    # Count words and estimate reading time
    word_count = len(markdown.split())
    reading_time_minutes = word_count // 200  # Average 200 WPM

    # Extract domain
    domain = extract_domain(url)

    return {
        'title': title,
        'author': author,
        'domain': domain,
        'published_at': pub_date or datetime.utcnow(),
        'word_count': word_count,
        'reading_time_minutes': reading_time_minutes,
        'url': url
    }


def identify_content_type(url: str, markdown: str) -> str:
    """
    Identify type of web content

    Args:
        url: Page URL
        markdown: Page content

    Returns:
        str: Content type ('blog_post', 'documentation', 'landing_page', 'article', 'other')
    """
    url_lower = url.lower()
    content_lower = markdown.lower()

    # Check URL patterns
    if '/blog/' in url_lower or '/post/' in url_lower or '/article/' in url_lower:
        return 'blog_post'

    if '/docs/' in url_lower or '/documentation/' in url_lower or '/api/' in url_lower:
        return 'documentation'

    if '/about' in url_lower or url_lower.endswith('/'):
        # Could be landing page
        if 'sign up' in content_lower or 'get started' in content_lower:
            return 'landing_page'

    # Check content patterns
    if 'table of contents' in content_lower or 'api reference' in content_lower:
        return 'documentation'

    if len(markdown) > 1000 and markdown.count('#') > 3:
        # Long form content with multiple headers
        return 'article'

    return 'other'


if __name__ == "__main__":
    # Test utilities
    test_markdown = """
    # How to Build a Second Brain

    Published on January 15, 2024

    By Dan Koe

    This is a comprehensive guide to building your second brain...

    ## Introduction

    The concept of a second brain...

    ## Step 1: Capture

    First, you need to capture ideas...
    """

    metadata = extract_article_metadata(test_markdown, "https://dankoe.com/blog/second-brain/")
    print(f"Extracted metadata: {metadata}")

    content_type = identify_content_type("https://dankoe.com/blog/second-brain/", test_markdown)
    print(f"Content type: {content_type}")

    cleaned = clean_markdown_content(test_markdown)
    print(f"Cleaned content:\n{cleaned[:200]}...")
```

---

## STEP 4: Create WebScraper Main Adapter

### File: `backend/scrapers/adapters/web.py`

```python
"""
Web/Blog Scraper Adapter
Implements BaseScraper interface with dual strategy:
1. Primary: Jina.ai Reader (FREE - 50K pages/month)
2. Fallback: ScraperAPI (PAID - $49/mo for JS rendering)

Scrapes thought leader blogs, documentation, articles
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..base import (
    BaseScraper,
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel
)
from ._jina_client import JinaReaderClient
from ._scraperapi_client import ScraperAPIClient
from ._content_extractor import (
    extract_article_metadata,
    clean_markdown_content,
    identify_content_type,
    extract_domain
)


class WebScraper(BaseScraper):
    """
    Web/Blog platform adapter with cost-optimized dual strategy

    Strategy:
    1. Try Jina.ai Reader first (FREE - 50K pages/month)
    2. Fall back to ScraperAPI only when:
       - Jina.ai fails (402, network error)
       - JavaScript rendering is required
       - Anti-bot protection detected

    Features:
    - Automatic HTML to Markdown conversion
    - Article metadata extraction (title, author, date)
    - Content type detection (blog, docs, article)
    - Rate limiting and error handling
    - Usage tracking for cost control
    """

    def __init__(self, use_scraperapi_fallback: bool = True):
        """
        Initialize Web scraper

        Args:
            use_scraperapi_fallback: Enable ScraperAPI as fallback (costs $)
        """
        self.jina_client = JinaReaderClient()
        self.scraperapi_client: Optional[ScraperAPIClient] = None
        self.use_scraperapi = use_scraperapi_fallback
        self._initialized = False

        # Stats tracking
        self.jina_successes = 0
        self.jina_failures = 0
        self.scraperapi_uses = 0
        self.total_requests = 0

    async def initialize(self) -> bool:
        """
        Initialize web scraper clients

        Returns:
            bool: True if initialized successfully
        """
        if self._initialized:
            return True

        # Jina.ai is always available (no auth needed)
        print("WebScraper: Jina.ai Reader client ready (FREE tier)")

        # Initialize ScraperAPI if configured and enabled
        if self.use_scraperapi:
            self.scraperapi_client = ScraperAPIClient()
            if self.scraperapi_client.api_key:
                print("WebScraper: ScraperAPI fallback available (PAID)")
            else:
                print("WebScraper: ScraperAPI not configured (no API key)")
                self.scraperapi_client = None
                self.use_scraperapi = False

        self._initialized = True
        return True

    async def health_check(self) -> dict:
        """
        Check Web scraper health status

        Returns:
            dict: Health metrics including usage stats
        """
        jina_stats = self.jina_client.get_usage_stats()

        status = "healthy"
        if jina_stats['consecutive_errors'] > 3:
            status = "degraded"
        if jina_stats['monthly_remaining'] < 100:
            status = "critical"  # Almost out of FREE tier

        scraperapi_stats = None
        if self.scraperapi_client:
            scraperapi_stats = self.scraperapi_client.get_usage_stats()

        return {
            "status": status,
            "authenticated": True,  # Jina.ai doesn't need auth
            "rate_limit_remaining": jina_stats['monthly_remaining'],
            "session_age_seconds": 0,
            "last_activity_seconds": 0,
            "error_count": jina_stats['error_count'],
            "jina_monthly_remaining": jina_stats['monthly_remaining'],
            "jina_monthly_used": jina_stats['requests_month'],
            "jina_successes": self.jina_successes,
            "jina_failures": self.jina_failures,
            "scraperapi_available": bool(self.scraperapi_client),
            "scraperapi_uses": self.scraperapi_uses,
            "scraperapi_stats": scraperapi_stats,
            "total_requests": self.total_requests,
            "message": f"Jina.ai: {jina_stats['monthly_remaining']}/50000 pages remaining"
        }

    async def extract(self, target: str, limit: int = 1) -> list[dict]:
        """
        Extract content from web URL(s)

        Args:
            target: URL or list of URLs (comma-separated)
            limit: Not used for web scraping (each URL is one page)

        Returns:
            list[dict]: Raw web content data
        """
        if not self._initialized:
            await self.initialize()

        # Handle single URL or multiple URLs
        if isinstance(target, str) and ',' in target:
            urls = [url.strip() for url in target.split(',')]
        elif isinstance(target, list):
            urls = target
        else:
            urls = [target]

        results = []
        for url in urls:
            print(f"Scraping: {url}")
            self.total_requests += 1

            # Try Jina.ai first (FREE)
            result = await self._try_jina(url)

            # Fall back to ScraperAPI if Jina fails
            if not result and self.use_scraperapi and self.scraperapi_client:
                print(f"Jina.ai failed, trying ScraperAPI fallback for {url}")
                result = self._try_scraperapi(url)
                if result:
                    self.scraperapi_uses += 1

            if result:
                results.append(result)
            else:
                print(f"Failed to scrape {url} with both methods")

        return results

    async def _try_jina(self, url: str) -> Optional[dict]:
        """Try to fetch URL with Jina.ai Reader"""
        try:
            result = await self.jina_client.fetch_as_markdown(url)
            if result:
                self.jina_successes += 1
                return result
            else:
                self.jina_failures += 1
                return None
        except Exception as e:
            self.jina_failures += 1
            print(f"Jina.ai error: {e}")
            return None

    def _try_scraperapi(self, url: str) -> Optional[dict]:
        """Try to fetch URL with ScraperAPI (PAID fallback)"""
        try:
            # Use JS rendering since Jina failed (likely dynamic content)
            result = self.scraperapi_client.fetch_page(url, render_js=True)
            return result
        except Exception as e:
            print(f"ScraperAPI error: {e}")
            return None

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Normalize web content to UnifiedContent schema

        Args:
            raw_data: Single page data dict from extract()

        Returns:
            UnifiedContent: Normalized content for PostgreSQL
        """
        url = raw_data.get('url', '')
        markdown = raw_data.get('markdown', '')

        # Clean the markdown
        markdown = clean_markdown_content(markdown)

        # Extract metadata from content
        metadata = extract_article_metadata(markdown, url)

        # Identify content type
        content_type = identify_content_type(url, markdown)

        # Build author model
        author = AuthorModel(
            id=metadata['author'],
            username=metadata['author'],
            display_name=metadata['author'],
            followers_count=0,  # Not available for web pages
            verified=False,
            profile_url=f"https://{metadata['domain']}"
        )

        # Build content model
        content = ContentModel(
            title=metadata['title'],
            body=markdown,
            word_count=metadata['word_count'],
            char_count=len(markdown),
            language="en"  # Assume English for now
        )

        # Build metrics model (web pages don't have engagement metrics)
        metrics = MetricsModel(
            likes=0,
            shares=0,
            comments=0,
            views=0,
            engagement_rate=0.0
        )

        # Empty analysis (to be filled by LLM later)
        analysis = AnalysisModel()

        # Build unified content
        unified = UnifiedContent(
            content_id=uuid4(),
            platform="web",
            source_url=url,
            author=author,
            content=content,
            metrics=metrics,
            analysis=analysis,
            embedding=[],  # To be filled by embedding service
            published_at=metadata['published_at'],
            scraped_at=datetime.utcnow(),
            metadata={
                'domain': metadata['domain'],
                'content_type': content_type,
                'reading_time_minutes': metadata['reading_time_minutes'],
                'scrape_source': raw_data.get('source', 'unknown'),
                'raw_title': raw_data.get('title', ''),
                'fetch_time': raw_data.get('fetch_time', datetime.utcnow()).isoformat()
            }
        )

        return unified

    async def scrape_blog(self, blog_url: str, limit: int = 10) -> list[UnifiedContent]:
        """
        Scrape multiple articles from a blog

        Args:
            blog_url: Blog URL (ideally /blog/ or /posts/ listing page)
            limit: Maximum articles to scrape

        Returns:
            list[UnifiedContent]: Normalized blog articles

        Note: This is a basic implementation. For better results,
        you'd want to parse the listing page and extract article URLs.
        """
        # For now, just scrape the main blog page
        # Future: Parse blog listing and extract individual article URLs
        return await self.scrape(blog_url, limit=1)

    async def scrape_authority(self, authority_name: str) -> list[UnifiedContent]:
        """
        Scrape content from a known thought leader

        Args:
            authority_name: Name like 'dankoe', 'jamesclear', 'calnewport'

        Returns:
            list[UnifiedContent]: Content from that authority
        """
        # Map authority names to their blog URLs
        authority_urls = {
            'dankoe': 'https://dankoe.com/blog/',
            'dan_koe': 'https://dankoe.com/blog/',
            'jamesclear': 'https://jamesclear.com/articles',
            'james_clear': 'https://jamesclear.com/articles',
            'calnewport': 'https://calnewport.com/blog/',
            'cal_newport': 'https://calnewport.com/blog/',
            'paulgraham': 'http://paulgraham.com/articles.html',
            'paul_graham': 'http://paulgraham.com/articles.html',
            'naval': 'https://nav.al/',
            'naval_ravikant': 'https://nav.al/'
        }

        authority_key = authority_name.lower().replace(' ', '_')

        if authority_key not in authority_urls:
            raise ValueError(
                f"Unknown authority: {authority_name}. "
                f"Known: {', '.join(authority_urls.keys())}"
            )

        url = authority_urls[authority_key]
        return await self.scrape(url, limit=1)

    def get_cost_breakdown(self) -> dict:
        """
        Get cost breakdown for scraping session

        Returns:
            dict: Cost information
        """
        # Jina.ai is FREE
        jina_cost = 0.0

        # ScraperAPI costs
        scraperapi_cost = 0.0
        if self.scraperapi_client:
            credits_used = self.scraperapi_client.credits_used
            # $49/100K credits = $0.00049 per credit
            scraperapi_cost = credits_used * 0.00049

        return {
            'jina_requests': self.jina_successes,
            'jina_cost': jina_cost,
            'scraperapi_requests': self.scraperapi_uses,
            'scraperapi_credits_used': self.scraperapi_client.credits_used if self.scraperapi_client else 0,
            'scraperapi_cost': round(scraperapi_cost, 4),
            'total_cost': round(jina_cost + scraperapi_cost, 4),
            'cost_savings': f"Saved ${round(self.jina_successes * 0.00049, 4)} by using Jina.ai FREE tier"
        }

    async def close(self):
        """Clean up resources"""
        await self.jina_client.close()
        print("WebScraper resources cleaned up")

    def __del__(self):
        """Cleanup on deletion"""
        pass


# Convenience function for quick testing
async def test_web_scraper():
    """Test WebScraper with a blog article"""
    scraper = WebScraper()

    print("Initializing WebScraper...")
    await scraper.initialize()

    print("\nChecking health...")
    health = await scraper.health_check()
    print(f"Health: {health}")

    # Test with a known blog article (Dan Koe's blog)
    test_url = "https://dankoe.com/blog/"

    print(f"\nScraping: {test_url}")
    articles = await scraper.scrape(test_url, limit=1)

    if articles:
        article = articles[0]
        print(f"\n--- Article Analysis ---")
        print(f"Platform: {article.platform}")
        print(f"Title: {article.content.title}")
        print(f"Author: {article.author.username}")
        print(f"Domain: {article.metadata.get('domain', '')}")
        print(f"Content Type: {article.metadata.get('content_type', '')}")
        print(f"Word Count: {article.content.word_count}")
        print(f"Reading Time: {article.metadata.get('reading_time_minutes', 0)} min")
        print(f"Scrape Source: {article.metadata.get('scrape_source', '')}")
        print(f"URL: {article.source_url}")
        print(f"\nContent preview:\n{article.content.body[:500]}...")
    else:
        print("Failed to scrape article")

    print(f"\nCost breakdown: {scraper.get_cost_breakdown()}")

    await scraper.close()
    return articles


if __name__ == "__main__":
    asyncio.run(test_web_scraper())
```

---

## STEP 5: Update Package Exports

### Update `backend/scrapers/adapters/__init__.py`:

```python
"""
Platform-specific scraper adapters
Each adapter implements the BaseScraper interface
"""

from .twitter import TwitterScraper
from .youtube import YouTubeScraper
from .reddit import RedditScraper
from .web import WebScraper

__all__ = ["TwitterScraper", "YouTubeScraper", "RedditScraper", "WebScraper"]
```

### Update `backend/scrapers/__init__.py`:

```python
"""
Unified Scraper - Platform Scrapers
Multi-platform content intelligence engine
"""

from .base import BaseScraper, UnifiedContent
from .adapters.twitter import TwitterScraper
from .adapters.youtube import YouTubeScraper
from .adapters.reddit import RedditScraper
from .adapters.web import WebScraper

__all__ = [
    "BaseScraper",
    "UnifiedContent",
    "TwitterScraper",
    "YouTubeScraper",
    "RedditScraper",
    "WebScraper"
]
```

---

## ERROR HANDLING PATTERNS

### Jina.ai Errors

```python
# Jina.ai specific errors
async def handle_jina_errors(url: str, jina_client: JinaReaderClient):
    try:
        result = await jina_client.fetch_as_markdown(url)
        return result
    except Exception as e:
        error_msg = str(e)

        if "402" in error_msg or "Payment Required" in error_msg:
            # FREE tier exhausted
            print("Jina.ai FREE tier limit reached (50K pages/month)")
            print("Options: Wait for reset or use ScraperAPI fallback")
            return None

        if "429" in error_msg:
            # Rate limited (rare with 200 req/min limit)
            print("Jina.ai rate limited. Waiting 60 seconds...")
            await asyncio.sleep(60)
            return await jina_client.fetch_as_markdown(url)

        if "Monthly" in error_msg:
            # Our own monthly limit check
            print("Monthly limit exceeded")
            return None

        # Generic error
        print(f"Jina.ai error: {e}")
        return None
```

### ScraperAPI Errors

```python
def handle_scraperapi_errors(url: str, client: ScraperAPIClient):
    try:
        result = client.fetch_page(url, render_js=True)
        return result
    except ValueError as e:
        # No API key
        print("ScraperAPI: API key not configured")
        return None
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status == 401:
            print("ScraperAPI: Invalid API key")
        elif status == 403:
            print("ScraperAPI: Account suspended or forbidden")
        elif status == 429:
            print("ScraperAPI: Credit limit reached")
        else:
            print(f"ScraperAPI: HTTP {status}")
        return None
    except Exception as e:
        print(f"ScraperAPI error: {e}")
        return None
```

### Network Errors

```python
import httpx

async def handle_network_errors(url: str):
    try:
        # ... fetch logic
        pass
    except httpx.ConnectError:
        print(f"Cannot connect to {url}. Check network.")
        return None
    except httpx.TimeoutException:
        print(f"Timeout fetching {url}. Page too slow.")
        return None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"Page not found: {url}")
        elif e.response.status_code == 403:
            print(f"Access forbidden: {url}")
        elif e.response.status_code == 500:
            print(f"Server error at {url}")
        return None
```

---

## RATE LIMITING STRATEGY

### Jina.ai (FREE tier)

```python
class JinaRateLimiter:
    """
    Jina.ai FREE Tier Limits:
    - 50,000 pages/month (hard limit)
    - 200 requests/minute (soft limit)
    - No daily limit

    Strategy:
    - Track monthly usage carefully
    - Warn at 90% usage
    - Auto-fallback to ScraperAPI at 100%
    - Minimum 300ms between requests (for 200/min)
    """

    def __init__(self):
        self.monthly_limit = 50000
        self.monthly_used = 0
        self.minute_requests = 0
        self.minute_limit = 200
        self.min_interval_ms = 300

    def can_request(self) -> bool:
        return self.monthly_used < self.monthly_limit

    def warning_level(self) -> str:
        usage_pct = self.monthly_used / self.monthly_limit
        if usage_pct >= 1.0:
            return "EXHAUSTED"
        elif usage_pct >= 0.95:
            return "CRITICAL"
        elif usage_pct >= 0.9:
            return "WARNING"
        elif usage_pct >= 0.75:
            return "CAUTION"
        return "OK"
```

### ScraperAPI (PAID fallback)

```python
class ScraperAPIRateLimiter:
    """
    ScraperAPI $49/mo Plan:
    - 100,000 credits/month
    - 1 credit = simple page
    - +5 credits = JS rendering
    - +25 credits = residential proxy

    Strategy:
    - Use ONLY when Jina.ai fails
    - Track credit usage
    - Alert at 80% usage
    - Prefer simple scrapes (1 credit) over JS rendering (6 credits)
    """

    def __init__(self):
        self.monthly_credits = 100000
        self.credits_used = 0

    def cost_per_request(self, render_js: bool = False) -> int:
        credits = 1
        if render_js:
            credits += 5
        return credits

    def remaining_requests(self, render_js: bool = False) -> int:
        cost = self.cost_per_request(render_js)
        remaining_credits = self.monthly_credits - self.credits_used
        return remaining_credits // cost
```

---

## COST OPTIMIZATION TIPS

1. **ALWAYS try Jina.ai first** - It's FREE (50K pages/month)

2. **Cache aggressively** - Don't re-scrape the same URL twice

3. **Batch requests** - Group URLs when possible

4. **Monitor usage**:
   ```python
   # Daily check
   jina_remaining = 50000 - jina_client.requests_made_month
   print(f"Jina.ai: {jina_remaining} pages remaining this month")

   # Cost tracking
   scraperapi_cost = scraperapi_client.credits_used * 0.00049
   print(f"ScraperAPI spend: ${scraperapi_cost:.4f}")
   ```

5. **Use ScraperAPI sparingly**:
   - Only for JS-rendered pages (React, Vue, Angular apps)
   - Only when Jina.ai explicitly fails
   - Prefer simple scrapes (1 credit) over JS rendering (6 credits)

6. **50K pages/month is PLENTY**:
   - 100 blog posts = 100 pages
   - 10 thought leaders = 1,000 articles
   - That's only 2% of your monthly FREE quota

---

## SUCCESS CRITERIA

### Functional Requirements
- [ ] Initialize WebScraper without errors
- [ ] Scrape blog article using Jina.ai (FREE)
- [ ] Convert HTML to clean Markdown
- [ ] Extract article metadata (title, author, date)
- [ ] Fall back to ScraperAPI when Jina.ai fails
- [ ] Track usage statistics (FREE tier remaining)
- [ ] All data normalized to UnifiedContent schema
- [ ] Cost breakdown calculation works

### Integration Requirements
- [ ] WebScraper implements BaseScraper ABC
- [ ] `health_check()` returns proper dict structure
- [ ] `extract()` returns list of raw page data
- [ ] `normalize()` returns UnifiedContent Pydantic model
- [ ] `scrape()` combines extract + normalize correctly

### Data Quality
- [ ] Article titles extracted accurately
- [ ] Article body converted to clean Markdown
- [ ] Author/domain extracted from URL
- [ ] Publication date detected (when available)
- [ ] Word count calculated correctly
- [ ] Content type identified (blog, docs, article)

### Cost Efficiency
- [ ] Jina.ai used as primary method
- [ ] ScraperAPI only used on Jina.ai failure
- [ ] Usage stats tracked accurately
- [ ] Cost breakdown calculated correctly
- [ ] Warnings issued when approaching FREE tier limit

### Testing Commands

```bash
# Install dependencies
cd backend
uv pip install httpx beautifulsoup4 markdownify lxml readability-lxml trafilatura

# Optional: Set ScraperAPI key for fallback
export SCRAPER_API_KEY=your_key_here

# Test basic import
python -c "from backend.scrapers.adapters.web import WebScraper; print('Import OK')"

# Test Jina.ai Reader (FREE)
python -c "
import asyncio
from backend.scrapers.adapters._jina_client import fetch_with_jina

async def test():
    result = await fetch_with_jina('https://example.com')
    if result:
        print(f'Title: {result[\"title\"]}')
        print(f'Words: {result[\"word_count\"]}')
        print(f'Source: {result[\"source\"]}')
        print(f'Preview: {result[\"markdown\"][:300]}')
    else:
        print('Failed')

asyncio.run(test())
"

# Test full WebScraper with blog article
python -c "
import asyncio
from backend.scrapers.adapters.web import test_web_scraper
asyncio.run(test_web_scraper())
"

# Test metadata extraction
python -c "
from backend.scrapers.adapters._content_extractor import extract_article_metadata
metadata = extract_article_metadata('# Test Article\n\nContent here', 'https://dankoe.com/blog/test/')
print(metadata)
"

# Health check and usage stats
python -c "
import asyncio
from backend.scrapers.adapters.web import WebScraper

async def check():
    s = WebScraper()
    await s.initialize()
    health = await s.health_check()
    print(f'Health: {health}')
    print(f'Cost breakdown: {s.get_cost_breakdown()}')

asyncio.run(check())
"

# Test ScraperAPI fallback (requires API key)
python -c "
from backend.scrapers.adapters._scraperapi_client import ScraperAPIClient
client = ScraperAPIClient()
print(f'ScraperAPI configured: {client.get_usage_stats()}')
"
```

---

## CRITICAL WARNINGS

1. **JINA.AI IS FREE - USE IT FIRST**: Don't waste money on ScraperAPI for static pages.

2. **50K PAGES/MONTH RESETS MONTHLY**: Track your usage. It's more than enough for most use cases.

3. **JINA.AI REQUIRES NO API KEY**: For basic usage. You can just call the endpoint.

4. **SCRAPERAPI COSTS MONEY**: $49/mo for 100K credits. Only use as fallback.

5. **JS-RENDERING COSTS 6x MORE**: A simple page = 1 credit. JS-rendered = 6 credits.

6. **CACHE YOUR RESULTS**: Don't re-scrape the same article. Store in PostgreSQL.

7. **RESPECT ROBOTS.TXT**: Even with Jina.ai, respect site policies.

8. **SOME SITES BLOCK SCRAPERS**: May need to use ScraperAPI's residential proxies (+25 credits).

9. **CONTENT MAY BE COPYRIGHTED**: Use scraped content for analysis, not republishing.

---

## ESTIMATED EFFORT

| Task | Time |
|------|------|
| Create directory structure | 5 min |
| Write _jina_client.py | 45 min |
| Write _scraperapi_client.py | 40 min |
| Write _content_extractor.py | 30 min |
| Write WebScraper wrapper | 60 min |
| Update package exports | 10 min |
| Install dependencies | 10 min |
| Test Jina.ai Reader | 15 min |
| Test ScraperAPI fallback | 15 min |
| Test metadata extraction | 15 min |
| Verify cost tracking | 10 min |
| Test blog scraping | 15 min |

**Total: 2-3 hours**

---

## SCRAPING THOUGHT LEADERS

### Known Authority URLs

```python
AUTHORITY_BLOGS = {
    'dankoe': 'https://dankoe.com/blog/',
    'jamesclear': 'https://jamesclear.com/articles',
    'calnewport': 'https://calnewport.com/blog/',
    'paulgraham': 'http://paulgraham.com/articles.html',
    'naval': 'https://nav.al/',
    'timbferriss': 'https://tim.blog/',
    'sethgodin': 'https://seths.blog/',
    'ryanholiday': 'https://ryanholiday.net/reading-list/',
}
```

### Example Usage

```python
# Scrape Dan Koe's blog
scraper = WebScraper()
await scraper.initialize()

articles = await scraper.scrape_authority('dankoe')
print(f"Scraped {len(articles)} articles from Dan Koe")

# Or direct URL
articles = await scraper.scrape('https://dankoe.com/blog/how-to-build-an-audience/')
```

---

## NEXT STEPS

Once WebScraper is operational, all four core platforms are complete:
- Twitter (Agent Beta) - Enterprise anti-detection
- YouTube (Agent Gamma) - Dual transcription strategy
- Reddit (Agent Delta) - VOC mining
- **Web/Blogs (Agent Epsilon) - Cost-optimized scraping**

Next: RAG integration (ChromaDB embeddings and semantic search)

---

## SUPPORT CONTACTS

- **Project Lead**: @iamcodio (GitHub)
- **Architecture Docs**: `/Users/kjd/01-projects/IAC-032-unified-scraper/CLAUDE.md`
- **Jina.ai Docs**: https://jina.ai/reader/
- **ScraperAPI Docs**: https://www.scraperapi.com/documentation/

---

**Remember**: This is the CHEAPEST scraper in your stack. $0/month for 50,000 pages. Use Jina.ai aggressively. Fall back to ScraperAPI only when absolutely necessary. Track your costs.

Good luck, Agent Epsilon.
