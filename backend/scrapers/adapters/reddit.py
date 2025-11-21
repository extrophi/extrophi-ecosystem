"""Reddit scraper using PRAW implementing BaseScraper interface."""

import os
from datetime import datetime
from typing import Any

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class RedditScraper(BaseScraper):
    """
    Reddit scraper using official PRAW API.

    Features:
    - OAuth authentication
    - Subreddit and user post extraction
    - Comment threading
    - Rate limit compliance (1000 req/10min)
    """

    def __init__(self) -> None:
        # Lazy import to avoid circular import issues with 'queue' module
        import praw

        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "IAC-032-unified-scraper/1.0"),
        )

    async def health_check(self) -> dict[str, Any]:
        """Verify Reddit API access."""
        try:
            # Test API access
            self.reddit.user.me()
            return {
                "status": "ok",
                "message": "Reddit API authenticated",
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "reddit",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "reddit",
            }

    async def extract(self, target: str, limit: int = 20) -> list[dict[str, Any]]:
        """
        Extract posts from subreddit or user.

        Args:
            target: Subreddit name (r/name) or username (u/name)
            limit: Maximum posts to fetch

        Returns:
            Raw post data as list of dicts
        """
        posts: list[dict[str, Any]] = []

        if target.startswith("r/"):
            subreddit_name = target[2:]
            subreddit = self.reddit.subreddit(subreddit_name)
            submissions = subreddit.hot(limit=limit)
        elif target.startswith("u/"):
            username = target[2:]
            redditor = self.reddit.redditor(username)
            submissions = redditor.submissions.new(limit=limit)
        else:
            # Default to subreddit
            subreddit = self.reddit.subreddit(target)
            submissions = subreddit.hot(limit=limit)

        for submission in submissions:
            posts.append(
                {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "subreddit": str(submission.subreddit),
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "permalink": submission.permalink,
                }
            )

        return posts

    async def normalize(self, raw_data: dict[str, Any]) -> UnifiedContent:
        """Convert raw Reddit data to UnifiedContent."""
        body = raw_data["selftext"] if raw_data["selftext"] else raw_data["title"]

        return UnifiedContent(
            platform="reddit",
            source_url=f"https://reddit.com{raw_data['permalink']}",
            author=AuthorModel(
                id=f"reddit_{raw_data['author']}",
                platform="reddit",
                username=raw_data["author"],
                display_name=raw_data["author"],
            ),
            content=ContentModel(
                title=raw_data["title"],
                body=body,
                word_count=len(body.split()),
            ),
            metrics=MetricsModel(
                likes=raw_data["score"],
                views=0,
                comments=raw_data["num_comments"],
                shares=0,
                engagement_rate=raw_data["upvote_ratio"],
            ),
            metadata={
                "subreddit": raw_data["subreddit"],
                "post_id": raw_data["id"],
                "created_utc": raw_data["created_utc"],
                "external_url": raw_data["url"],
            },
        )
