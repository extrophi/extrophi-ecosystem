"""
Elon Musk Twitter scraper using twscrape (free, no API required).

Scrapes @elonmusk for innovation insights, first principles thinking,
and yes, the memes. Limits to 1,000 tweets to avoid drowning in content.
"""

import re
from datetime import datetime
from typing import Any

from twscrape import API

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class ElonScraper(BaseScraper):
    """
    Specialized scraper for @elonmusk tweets with categorization.

    Features:
    - Free scraping via twscrape (no API keys required)
    - Innovation vs meme classification
    - Theme detection: Business, Tech, Mars, Problem-solving
    - First principles thinking extraction
    - Limited to 1,000 tweets (he tweets A LOT)

    Categories:
    - Innovation: Product launches, tech breakthroughs, Tesla/SpaceX updates
    - Business: Company strategy, market insights, regulatory commentary
    - Mars: SpaceX, Mars colonization, space exploration
    - Problem-solving: First principles thinking, engineering challenges
    - Memes: Everything else (let's be honest, it's a lot)
    """

    # Theme detection patterns
    THEMES = {
        "business": [
            r"\b(revenue|profit|market|strategy|competitor|acquisition|investment|shareholders|SEC)\b",
            r"\b(Tesla|SpaceX|Neuralink|Boring Company|X\.com|Twitter)\b",
            r"\b(IPO|stock|valuation|merger|quarterly|earnings)\b",
        ],
        "tech": [
            r"\b(AI|artificial intelligence|neural network|AGI|LLM|machine learning)\b",
            r"\b(battery|electric|autonomous|self-driving|FSD|autopilot)\b",
            r"\b(satellite|Starlink|internet|bandwidth|latency)\b",
            r"\b(robotics|Optimus|humanoid|automation)\b",
            r"\b(solar|energy|sustainable|renewable|grid)\b",
        ],
        "mars": [
            r"\b(Mars|Red Planet|SpaceX|Starship|rocket|launch|orbit)\b",
            r"\b(colonization|multi-planetary|interplanetary|space travel)\b",
            r"\b(Falcon|Dragon|Raptor|Starbase|Boca Chica)\b",
        ],
        "problem_solving": [
            r"\b(first principles|from scratch|fundamental|physics|engineering)\b",
            r"\b(optimize|efficiency|improvement|solution|iterate|prototype)\b",
            r"\b(constraint|limitation|bottleneck|breakthrough|innovation)\b",
        ],
        "meme": [
            r"😂|🤣|💀|🔥|👀|🚀",  # Emoji indicators
            r"\b(lol|lmao|bruh|based|cringe|ratio)\b",
            r"@\w+\s+(is|are)\s+(wrong|right|dumb|smart)",  # Replies/callouts
        ],
    }

    def __init__(self):
        """Initialize twscrape API."""
        self.api = API()
        self.username = "elonmusk"
        self.max_tweets = 1000  # Hard limit - he tweets too much
        self.stats = {
            "total_scraped": 0,
            "innovation": 0,
            "memes": 0,
            "themes": {"business": 0, "tech": 0, "mars": 0, "problem_solving": 0},
        }

    async def health_check(self) -> dict:
        """Verify scraper is ready."""
        return {
            "status": "ok",
            "message": "Elon Musk scraper initialized (twscrape)",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "twitter",
            "target": f"@{self.username}",
            "max_tweets": self.max_tweets,
        }

    async def extract(self, target: str = "elonmusk", limit: int = 1000) -> list[dict]:
        """
        Extract tweets from @elonmusk.

        Args:
            target: Twitter username (default: elonmusk)
            limit: Max tweets to fetch (capped at 1000)

        Returns:
            List of raw tweet dictionaries
        """
        # Override target to always be elonmusk
        target = "elonmusk"
        limit = min(limit, self.max_tweets)  # Cap at 1,000

        tweets = []
        try:
            # Use twscrape to fetch user timeline
            async for tweet in self.api.user_tweets(target, limit=limit):
                tweet_data = {
                    "id": str(tweet.id),
                    "text": tweet.rawContent,
                    "author_id": tweet.user.username,
                    "author_name": tweet.user.displayname,
                    "created_at": tweet.date.isoformat() if tweet.date else datetime.utcnow().isoformat(),
                    "public_metrics": {
                        "like_count": tweet.likeCount or 0,
                        "retweet_count": tweet.retweetCount or 0,
                        "reply_count": tweet.replyCount or 0,
                        "view_count": tweet.viewCount or 0,
                    },
                    "url": tweet.url,
                    "is_retweet": tweet.retweetedTweet is not None,
                    "is_reply": tweet.inReplyToTweetId is not None,
                }
                tweets.append(tweet_data)
                self.stats["total_scraped"] += 1

        except Exception as e:
            print(f"Error scraping @{target}: {e}")
            # Return whatever we got before the error
            pass

        return tweets

    def _detect_themes(self, text: str) -> list[str]:
        """
        Detect themes in tweet text.

        Returns:
            List of detected themes (business, tech, mars, problem_solving)
        """
        detected = []
        text_lower = text.lower()

        for theme, patterns in self.THEMES.items():
            if theme == "meme":
                continue  # Handle memes separately

            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected.append(theme)
                    self.stats["themes"][theme] = self.stats["themes"].get(theme, 0) + 1
                    break

        return detected

    def _is_meme(self, text: str) -> bool:
        """
        Classify if tweet is a meme/joke vs substantive content.

        Heuristics:
        - Contains common meme emojis (🚀, 💀, 😂)
        - Short tweets (<50 chars) without URLs
        - Contains meme language (lol, lmao, ratio, based)
        - All caps with exclamation marks

        Returns:
            True if likely a meme, False if likely insight
        """
        text_lower = text.lower()

        # Check meme patterns
        for pattern in self.THEMES["meme"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.stats["memes"] += 1
                return True

        # Short tweets without substance
        if len(text) < 50 and not re.search(r"https?://", text):
            self.stats["memes"] += 1
            return True

        # All caps with multiple exclamation marks (likely meme/rant)
        if text.isupper() and text.count("!") >= 2:
            self.stats["memes"] += 1
            return True

        # Default to innovation/insight
        self.stats["innovation"] += 1
        return False

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Convert raw tweet to UnifiedContent with categorization.

        Adds metadata:
        - themes: List of detected themes
        - is_meme: Boolean classification
        - category: "innovation" or "meme"
        - source: "elon" (for filtering in analysis)
        """
        text = raw_data["text"]
        themes = self._detect_themes(text)
        is_meme = self._is_meme(text)

        return UnifiedContent(
            platform="twitter",
            source_url=raw_data.get("url", f"https://twitter.com/{raw_data['author_id']}/status/{raw_data['id']}"),
            author=AuthorModel(
                id=raw_data["author_id"],
                platform="twitter",
                username=raw_data["author_id"],
                display_name=raw_data.get("author_name"),
            ),
            content=ContentModel(
                title=None,
                body=text,
                word_count=len(text.split()),
            ),
            metrics=MetricsModel(
                likes=raw_data["public_metrics"]["like_count"],
                views=raw_data["public_metrics"].get("view_count", 0),
                comments=raw_data["public_metrics"]["reply_count"],
                shares=raw_data["public_metrics"]["retweet_count"],
                engagement_rate=0.0,  # Can calculate if needed
            ),
            metadata={
                "tweet_id": raw_data["id"],
                "created_at": raw_data["created_at"],
                "source": "elon",  # Special tag for Elon content
                "themes": themes,
                "is_meme": is_meme,
                "category": "meme" if is_meme else "innovation",
                "is_retweet": raw_data.get("is_retweet", False),
                "is_reply": raw_data.get("is_reply", False),
            },
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get scraping statistics.

        Returns:
            Dict with:
            - total_scraped: Total tweets collected
            - innovation: Count of substantive tweets
            - memes: Count of meme/joke tweets
            - meme_ratio: Percentage of tweets that are memes
            - themes: Breakdown by theme (business, tech, mars, problem_solving)
        """
        meme_ratio = (self.stats["memes"] / self.stats["total_scraped"] * 100
                     if self.stats["total_scraped"] > 0 else 0)

        return {
            "total_scraped": self.stats["total_scraped"],
            "innovation": self.stats["innovation"],
            "memes": self.stats["memes"],
            "meme_ratio": f"{meme_ratio:.1f}%",
            "themes": self.stats["themes"],
            "top_theme": max(self.stats["themes"].items(), key=lambda x: x[1])[0]
            if any(self.stats["themes"].values())
            else "none",
        }
