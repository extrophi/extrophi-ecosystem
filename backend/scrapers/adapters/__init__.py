"""Platform-specific scraper adapters."""
from backend.scrapers.adapters.reddit import RedditScraper
from backend.scrapers.adapters.twitter import TwitterScraper
from backend.scrapers.adapters.web import WebScraper
from backend.scrapers.adapters.youtube import YouTubeScraper

__all__ = ["TwitterScraper", "RedditScraper", "YouTubeScraper", "WebScraper"]
