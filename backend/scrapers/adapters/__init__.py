"""Platform-specific scraper adapters."""

# Lazy imports to avoid loading all dependencies at once
# Import scrapers individually when needed

__all__ = ["TwitterScraper", "RedditScraper", "YouTubeScraper", "WebScraper"]


def __getattr__(name):
    """Lazy load scraper classes to avoid import errors when dependencies missing."""
    if name == "TwitterScraper":
        from backend.scrapers.adapters.twitter import TwitterScraper
        return TwitterScraper
    elif name == "RedditScraper":
        from backend.scrapers.adapters.reddit import RedditScraper
        return RedditScraper
    elif name == "YouTubeScraper":
        from backend.scrapers.adapters.youtube import YouTubeScraper
        return YouTubeScraper
    elif name == "WebScraper":
        from backend.scrapers.adapters.web import WebScraper
        return WebScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
