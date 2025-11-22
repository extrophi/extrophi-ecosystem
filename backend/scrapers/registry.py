"""Scraper registry for platform adapters."""

from typing import Type

from backend.scrapers.base import BaseScraper

# Global scraper registry
_SCRAPER_REGISTRY: dict[str, Type[BaseScraper]] = {}


def register_scraper(platform: str, scraper_class: Type[BaseScraper]) -> None:
    """
    Register a scraper class for a platform.

    Args:
        platform: Platform identifier (twitter, youtube, reddit, web)
        scraper_class: Class that implements BaseScraper
    """
    _SCRAPER_REGISTRY[platform.lower()] = scraper_class


def get_scraper(platform: str) -> BaseScraper:
    """
    Get scraper instance for a platform.

    Args:
        platform: Platform identifier

    Returns:
        Instantiated scraper

    Raises:
        ValueError: If platform not registered
    """
    platform = platform.lower()

    if platform not in _SCRAPER_REGISTRY:
        raise ValueError(
            f"No scraper registered for platform '{platform}'. "
            f"Available: {list(_SCRAPER_REGISTRY.keys())}"
        )

    scraper_class = _SCRAPER_REGISTRY[platform]
    return scraper_class()


def list_scrapers() -> list[str]:
    """List all registered platform scrapers."""
    return list(_SCRAPER_REGISTRY.keys())


# Auto-register all adapters on import
def _auto_register():
    """Automatically register all available scrapers."""
    try:
        from backend.scrapers.adapters.twitter import TwitterScraper

        register_scraper("twitter", TwitterScraper)
    except ImportError:
        pass

    try:
        from backend.scrapers.adapters.reddit import RedditScraper

        register_scraper("reddit", RedditScraper)
    except ImportError:
        pass

    try:
        from backend.scrapers.adapters.youtube import YouTubeScraper

        register_scraper("youtube", YouTubeScraper)
    except ImportError:
        pass

    try:
        from backend.scrapers.adapters.web import WebScraper

        register_scraper("web", WebScraper)
    except ImportError:
        pass

    try:
        from backend.scrapers.adapters.throssell import ThrossellScraper

        register_scraper("throssell", ThrossellScraper)
    except ImportError:
        pass


# Auto-register on module load
_auto_register()
