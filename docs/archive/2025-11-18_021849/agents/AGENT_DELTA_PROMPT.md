# AGENT DELTA: Reddit Scraper Implementation

## MISSION: Extract Community Intelligence from Reddit

**Agent ID**: Delta
**Role**: Reddit Platform Adapter
**Priority**: HIGH (Best source for VOC - Voice of Customer data)
**Estimated Time**: 2-3 hours

---

## EXECUTIVE SUMMARY

Build a Reddit scraper using PRAW (Python Reddit API Wrapper) to extract posts, comments, and engagement metrics from subreddits. Reddit is THE source for authentic Voice of Customer (VOC) data - unfiltered pain points, desires, and real discussions.

**Key Insight**: Reddit's FREE OAuth tier provides 1,000 requests per 10 minutes. That's 6,000 posts + comments per hour at zero cost. Pain point extraction from 1-3 star discussions reveals authentic customer problems.

**Architecture**: Implement `BaseScraper` interface from Agent Beta, normalizing Reddit data (posts + comments) into the `UnifiedContent` schema for PostgreSQL storage.

---

## REDDIT API SETUP (ONE-TIME)

### Step 1: Create Reddit Application

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: `IAC-032-Unified-Scraper`
   - **Type**: Select "script" (for personal use)
   - **Description**: `Content intelligence scraper for research`
   - **Redirect URI**: `http://localhost:8080` (not used for script apps)
4. Click "Create App"
5. Note these values:
   - **Client ID**: Under the app name (short alphanumeric string)
   - **Client Secret**: The "secret" field

### Step 2: Environment Variables

```bash
# Add to .env file
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=IAC-032-UnifiedScraper/1.0 by u/iamcodio
```

**IMPORTANT**: User agent MUST be unique and descriptive. Reddit blocks generic user agents.

---

## DEPENDENCIES TO ADD

### Update `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...

    # Reddit API (Official Wrapper)
    "praw>=7.7.0",
    "prawcore>=2.3.0",

    # Rate limiting helpers
    "ratelimit>=2.2.1",
]
```

---

## FILES TO CREATE

### Directory Structure
```
backend/
  scrapers/
    adapters/
      reddit.py                    # RedditScraper (main adapter)
      _reddit_client.py            # PRAW client wrapper with rate limiting
```

---

## STEP 1: Create PRAW Client Wrapper

### File: `backend/scrapers/adapters/_reddit_client.py`

```python
"""
Reddit PRAW Client Wrapper
Handles authentication, rate limiting, and connection management
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Iterator

import praw
from praw.models import Subreddit, Submission, Comment
from prawcore.exceptions import (
    ResponseException,
    RequestException,
    TooManyRequests
)


class RedditClient:
    """
    PRAW client wrapper with built-in rate limiting and error handling

    Reddit API Limits (OAuth):
    - 60 requests per minute (FREE tier)
    - 1,000 requests per 10 minutes
    - No daily limit (practical limit is hourly)

    Best Practice:
    - Respect rate limits to avoid temporary bans
    - Use unique, descriptive user agent
    - Cache results when possible
    """

    def __init__(self):
        """Initialize PRAW Reddit client"""
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv(
            "REDDIT_USER_AGENT",
            "IAC-032-UnifiedScraper/1.0 by u/iamcodio"
        )

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Reddit credentials not found. Set REDDIT_CLIENT_ID and "
                "REDDIT_CLIENT_SECRET environment variables."
            )

        # Initialize PRAW in read-only mode (no user authentication needed)
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )

        # Rate limiting tracking
        self.requests_made = 0
        self.window_start = datetime.utcnow()
        self.max_per_minute = 60
        self.max_per_10min = 1000

        # Connection health
        self.last_request_time = datetime.utcnow()
        self.error_count = 0
        self.consecutive_errors = 0

    def _check_rate_limit(self):
        """Check and respect rate limits"""
        now = datetime.utcnow()

        # Reset window if 10 minutes passed
        if (now - self.window_start) >= timedelta(minutes=10):
            self.requests_made = 0
            self.window_start = now

        # Check if we're hitting limits
        if self.requests_made >= self.max_per_10min:
            wait_time = 600 - (now - self.window_start).seconds
            raise TooManyRequests(
                f"Rate limit reached. Wait {wait_time} seconds."
            )

        self.requests_made += 1
        self.last_request_time = now

    def _handle_error(self, error: Exception):
        """Track errors and determine if we should retry"""
        self.error_count += 1
        self.consecutive_errors += 1

        if self.consecutive_errors > 5:
            raise Exception(
                f"Too many consecutive errors ({self.consecutive_errors}). "
                f"Check your credentials and network."
            )

    def _reset_error_streak(self):
        """Reset consecutive error counter on success"""
        self.consecutive_errors = 0

    def get_subreddit(self, name: str) -> Subreddit:
        """
        Get a subreddit object

        Args:
            name: Subreddit name (without r/)

        Returns:
            Subreddit: PRAW Subreddit object
        """
        self._check_rate_limit()
        try:
            subreddit = self.reddit.subreddit(name)
            self._reset_error_streak()
            return subreddit
        except Exception as e:
            self._handle_error(e)
            raise

    def get_hot_posts(self, subreddit_name: str, limit: int = 25) -> Iterator[Submission]:
        """
        Get hot posts from a subreddit

        Args:
            subreddit_name: Name of subreddit
            limit: Maximum posts to fetch

        Yields:
            Submission: PRAW Submission objects
        """
        self._check_rate_limit()
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.hot(limit=limit):
                yield post
            self._reset_error_streak()
        except Exception as e:
            self._handle_error(e)
            raise

    def get_new_posts(self, subreddit_name: str, limit: int = 25) -> Iterator[Submission]:
        """
        Get newest posts from a subreddit

        Args:
            subreddit_name: Name of subreddit
            limit: Maximum posts to fetch

        Yields:
            Submission: PRAW Submission objects
        """
        self._check_rate_limit()
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.new(limit=limit):
                yield post
            self._reset_error_streak()
        except Exception as e:
            self._handle_error(e)
            raise

    def get_top_posts(
        self,
        subreddit_name: str,
        time_filter: str = "week",
        limit: int = 25
    ) -> Iterator[Submission]:
        """
        Get top posts from a subreddit

        Args:
            subreddit_name: Name of subreddit
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            limit: Maximum posts to fetch

        Yields:
            Submission: PRAW Submission objects
        """
        self._check_rate_limit()
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.top(time_filter=time_filter, limit=limit):
                yield post
            self._reset_error_streak()
        except Exception as e:
            self._handle_error(e)
            raise

    def get_post_comments(
        self,
        submission: Submission,
        limit: int = 50,
        depth: int = 2
    ) -> list[dict]:
        """
        Get comments for a submission with threading preserved

        Args:
            submission: PRAW Submission object
            limit: Maximum top-level comments
            depth: How deep to traverse comment tree

        Returns:
            list[dict]: Nested comment data
        """
        self._check_rate_limit()
        try:
            # Replace MoreComments objects
            submission.comments.replace_more(limit=0)

            comments = []
            for i, top_comment in enumerate(submission.comments[:limit]):
                if isinstance(top_comment, Comment):
                    comment_data = self._extract_comment_tree(top_comment, depth)
                    comments.append(comment_data)

            self._reset_error_streak()
            return comments
        except Exception as e:
            self._handle_error(e)
            raise

    def _extract_comment_tree(self, comment: Comment, depth: int) -> dict:
        """
        Recursively extract comment tree

        Args:
            comment: PRAW Comment object
            depth: Remaining depth to traverse

        Returns:
            dict: Comment data with nested replies
        """
        comment_data = {
            'id': comment.id,
            'author': str(comment.author) if comment.author else '[deleted]',
            'body': comment.body,
            'score': comment.score,
            'created_utc': datetime.utcfromtimestamp(comment.created_utc),
            'is_submitter': comment.is_submitter,
            'edited': comment.edited,
            'replies': []
        }

        # Get nested replies if depth allows
        if depth > 0 and hasattr(comment, 'replies'):
            for reply in comment.replies:
                if isinstance(reply, Comment):
                    reply_data = self._extract_comment_tree(reply, depth - 1)
                    comment_data['replies'].append(reply_data)

        return comment_data

    def search_subreddit(
        self,
        subreddit_name: str,
        query: str,
        limit: int = 25
    ) -> Iterator[Submission]:
        """
        Search posts within a subreddit

        Args:
            subreddit_name: Name of subreddit
            query: Search query
            limit: Maximum results

        Yields:
            Submission: Matching posts
        """
        self._check_rate_limit()
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.search(query, limit=limit):
                yield post
            self._reset_error_streak()
        except Exception as e:
            self._handle_error(e)
            raise

    def get_health_status(self) -> dict:
        """Get client health status"""
        now = datetime.utcnow()
        window_elapsed = (now - self.window_start).seconds
        remaining_requests = max(0, self.max_per_10min - self.requests_made)

        return {
            'authenticated': True,  # Read-only doesn't need user auth
            'requests_made': self.requests_made,
            'requests_remaining': remaining_requests,
            'window_elapsed_seconds': window_elapsed,
            'window_reset_seconds': max(0, 600 - window_elapsed),
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'last_request': self.last_request_time.isoformat()
        }


# Convenience function
def create_reddit_client() -> RedditClient:
    """Create and validate Reddit client"""
    client = RedditClient()

    # Test connection
    try:
        _ = client.reddit.read_only
        print("Reddit client initialized successfully (read-only mode)")
    except Exception as e:
        print(f"Reddit client initialization failed: {e}")
        raise

    return client


if __name__ == "__main__":
    # Test Reddit client
    client = create_reddit_client()

    print("Health status:", client.get_health_status())

    print("\nFetching hot posts from r/productivity...")
    for i, post in enumerate(client.get_hot_posts("productivity", limit=3)):
        print(f"{i+1}. {post.title[:60]}...")
        print(f"   Score: {post.score}, Comments: {post.num_comments}")
```

---

## STEP 2: Create RedditScraper Main Adapter

### File: `backend/scrapers/adapters/reddit.py`

```python
"""
Reddit Scraper Adapter
Implements BaseScraper interface using PRAW (Python Reddit API Wrapper)

Reddit provides authentic Voice of Customer (VOC) data:
- Pain points from frustrated users (1-3 star discussions)
- Desires from aspirational posts (5-star discussions)
- Real-world use cases and workflows
- Unfiltered opinions and critiques
"""

import asyncio
from datetime import datetime
from typing import Any, Optional, Literal
from uuid import uuid4

from ..base import (
    BaseScraper,
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel
)
from ._reddit_client import RedditClient, create_reddit_client


class RedditScraper(BaseScraper):
    """
    Reddit platform adapter with PRAW integration

    Features:
    - Hot, New, Top post extraction
    - Comment threading with depth control
    - Subreddit search
    - Built-in rate limiting (1,000 req/10min FREE)
    - Pain point / desire extraction (VOC mining)
    """

    def __init__(self):
        """Initialize Reddit scraper"""
        self.client: Optional[RedditClient] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize Reddit client

        Returns:
            bool: True if initialized successfully
        """
        if self._initialized and self.client:
            return True

        try:
            self.client = create_reddit_client()
            self._initialized = True
            print("RedditScraper initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize RedditScraper: {e}")
            return False

    async def health_check(self) -> dict:
        """
        Check Reddit scraper health status

        Returns:
            dict: Health metrics including rate limits and errors
        """
        if not self.client:
            return {
                "status": "unhealthy",
                "authenticated": False,
                "rate_limit_remaining": 0,
                "session_age_seconds": 0,
                "last_activity_seconds": 0,
                "error_count": 0,
                "message": "Client not initialized"
            }

        health = self.client.get_health_status()

        status = "healthy"
        if health['consecutive_errors'] > 3:
            status = "degraded"
        if health['consecutive_errors'] > 5:
            status = "unhealthy"

        return {
            "status": status,
            "authenticated": health['authenticated'],
            "rate_limit_remaining": health['requests_remaining'],
            "session_age_seconds": health['window_elapsed_seconds'],
            "last_activity_seconds": (
                datetime.utcnow() -
                datetime.fromisoformat(health['last_request'])
            ).total_seconds(),
            "error_count": health['error_count'],
            "window_reset_seconds": health['window_reset_seconds'],
            "message": f"Reddit API operational. {health['requests_remaining']} requests remaining."
        }

    async def extract(
        self,
        target: str,
        limit: int = 50,
        sort: Literal["hot", "new", "top"] = "hot",
        time_filter: str = "week",
        include_comments: bool = True,
        comment_limit: int = 10,
        comment_depth: int = 2
    ) -> list[dict]:
        """
        Extract posts from a subreddit

        Args:
            target: Subreddit name (without r/)
            limit: Maximum posts to extract (default 50)
            sort: Sorting method ('hot', 'new', 'top')
            time_filter: For 'top' sort - 'hour', 'day', 'week', 'month', 'year', 'all'
            include_comments: Whether to fetch comments (slower but richer data)
            comment_limit: Max top-level comments per post
            comment_depth: Comment tree depth

        Returns:
            list[dict]: Raw Reddit post data with optional comments
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Reddit client")

        print(f"Extracting {limit} {sort} posts from r/{target}...")

        # Get posts based on sort method
        if sort == "hot":
            posts_generator = self.client.get_hot_posts(target, limit)
        elif sort == "new":
            posts_generator = self.client.get_new_posts(target, limit)
        elif sort == "top":
            posts_generator = self.client.get_top_posts(target, time_filter, limit)
        else:
            posts_generator = self.client.get_hot_posts(target, limit)

        raw_data = []
        for i, submission in enumerate(posts_generator):
            print(f"Processing post {i+1}/{limit}: {submission.title[:50]}...")

            post_data = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'selftext': submission.selftext,
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': datetime.utcfromtimestamp(submission.created_utc),
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'is_self': submission.is_self,
                'link_flair_text': submission.link_flair_text,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'stickied': submission.stickied,
                'subreddit': str(submission.subreddit),
                'subreddit_subscribers': submission.subreddit.subscribers,
                'comments': []
            }

            # Fetch comments if requested
            if include_comments and submission.num_comments > 0:
                try:
                    post_data['comments'] = self.client.get_post_comments(
                        submission,
                        limit=comment_limit,
                        depth=comment_depth
                    )
                except Exception as e:
                    print(f"Failed to fetch comments for {submission.id}: {e}")

            raw_data.append(post_data)

        return raw_data

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Normalize Reddit post data to UnifiedContent schema

        Args:
            raw_data: Single post dictionary from extract()

        Returns:
            UnifiedContent: Normalized content for PostgreSQL
        """
        # Build author model
        author = AuthorModel(
            id=raw_data.get('author', 'unknown'),
            username=raw_data.get('author', 'unknown'),
            display_name=raw_data.get('author', 'unknown'),
            followers_count=0,  # Reddit doesn't expose this easily
            verified=False,
            profile_url=f"https://reddit.com/u/{raw_data.get('author', 'unknown')}"
        )

        # Build content model
        # Reddit posts have title + optional body (selftext)
        title = raw_data.get('title', 'Untitled')
        body = raw_data.get('selftext', '')

        # If no selftext (link post), use title as body
        if not body:
            body = title

        # Append comment text for richer content
        comments_text = self._flatten_comments(raw_data.get('comments', []))
        if comments_text:
            body = f"{body}\n\n--- Comments ---\n{comments_text}"

        content = ContentModel(
            title=title,
            body=body,
            word_count=len(body.split()),
            char_count=len(body),
            language="en"  # Reddit is primarily English
        )

        # Build metrics model
        score = raw_data.get('score', 0)
        upvote_ratio = raw_data.get('upvote_ratio', 0.5)
        num_comments = raw_data.get('num_comments', 0)

        # Reddit engagement rate: (upvotes + comments) / subreddit size
        subreddit_size = raw_data.get('subreddit_subscribers', 1)
        total_engagement = score + num_comments
        engagement_rate = (total_engagement / max(subreddit_size, 1)) * 100

        metrics = MetricsModel(
            likes=score,  # Reddit score (upvotes - downvotes)
            shares=0,  # Reddit doesn't track shares
            comments=num_comments,
            views=0,  # Reddit doesn't expose view count for most posts
            engagement_rate=round(engagement_rate, 6)  # Very small for large subreddits
        )

        # Empty analysis (to be filled by LLM later)
        analysis = AnalysisModel()

        # Build unified content
        unified = UnifiedContent(
            content_id=uuid4(),
            platform="reddit",
            source_url=raw_data.get('permalink', ''),
            author=author,
            content=content,
            metrics=metrics,
            analysis=analysis,
            embedding=[],  # To be filled by embedding service
            published_at=raw_data.get('created_utc', datetime.utcnow()),
            scraped_at=datetime.utcnow(),
            metadata={
                'post_id': raw_data.get('id'),
                'subreddit': raw_data.get('subreddit', ''),
                'subreddit_subscribers': raw_data.get('subreddit_subscribers', 0),
                'upvote_ratio': raw_data.get('upvote_ratio', 0.5),
                'is_self_post': raw_data.get('is_self', True),
                'link_url': raw_data.get('url', '') if not raw_data.get('is_self', True) else '',
                'flair': raw_data.get('link_flair_text', ''),
                'is_nsfw': raw_data.get('over_18', False),
                'is_spoiler': raw_data.get('spoiler', False),
                'is_stickied': raw_data.get('stickied', False),
                'comment_count': len(raw_data.get('comments', [])),
                'comments': raw_data.get('comments', [])  # Store full comment tree
            }
        )

        return unified

    def _flatten_comments(self, comments: list[dict], prefix: str = "") -> str:
        """
        Flatten nested comment tree to text

        Args:
            comments: Nested comment list
            prefix: Indentation prefix for nesting

        Returns:
            str: Flattened comment text
        """
        text_parts = []

        for comment in comments:
            author = comment.get('author', '[deleted]')
            body = comment.get('body', '')
            score = comment.get('score', 0)

            # Format comment
            comment_text = f"{prefix}> u/{author} ({score} pts):\n{prefix}> {body}\n"
            text_parts.append(comment_text)

            # Recursively add replies
            if comment.get('replies'):
                nested_text = self._flatten_comments(
                    comment['replies'],
                    prefix=prefix + "  "
                )
                text_parts.append(nested_text)

        return "\n".join(text_parts)

    async def search_subreddit(
        self,
        subreddit: str,
        query: str,
        limit: int = 25
    ) -> list[UnifiedContent]:
        """
        Search posts within a subreddit

        Args:
            subreddit: Subreddit name
            query: Search query
            limit: Maximum results

        Returns:
            list[UnifiedContent]: Normalized search results
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Reddit client")

        print(f"Searching r/{subreddit} for '{query}'...")

        raw_posts = []
        for submission in self.client.search_subreddit(subreddit, query, limit):
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'selftext': submission.selftext,
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': datetime.utcfromtimestamp(submission.created_utc),
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'is_self': submission.is_self,
                'link_flair_text': submission.link_flair_text,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'stickied': submission.stickied,
                'subreddit': str(submission.subreddit),
                'subreddit_subscribers': submission.subreddit.subscribers,
                'comments': []  # Skip comments for search (faster)
            }
            raw_posts.append(post_data)

        # Normalize all posts
        normalized = []
        for post in raw_posts:
            content = await self.normalize(post)
            normalized.append(content)

        return normalized

    async def extract_pain_points(
        self,
        subreddit: str,
        limit: int = 50
    ) -> list[UnifiedContent]:
        """
        Extract posts with negative sentiment (pain points / frustrations)

        Args:
            subreddit: Subreddit to analyze
            limit: Maximum posts

        Returns:
            list[UnifiedContent]: Posts likely containing pain points

        Pain point indicators:
        - Low upvote ratio (<0.7)
        - Keywords: "frustrated", "hate", "problem", "issue", "can't", "won't"
        - Question posts (asking for help)
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Reddit client")

        print(f"Mining pain points from r/{subreddit}...")

        # Get new posts (more likely to have problems)
        raw_posts = await self.extract(
            subreddit,
            limit=limit * 2,  # Get more to filter
            sort="new",
            include_comments=True
        )

        # Filter for pain point indicators
        pain_keywords = [
            'help', 'problem', 'issue', 'frustrated', 'struggling',
            'can\'t', 'won\'t', 'doesn\'t work', 'broken', 'hate',
            'annoying', 'why won\'t', 'how do i', 'advice needed'
        ]

        pain_posts = []
        for post in raw_posts:
            title_lower = post['title'].lower()
            body_lower = post.get('selftext', '').lower()
            combined = title_lower + " " + body_lower

            # Check for pain indicators
            is_pain_point = any(keyword in combined for keyword in pain_keywords)
            is_low_ratio = post.get('upvote_ratio', 1.0) < 0.7
            is_question = post['title'].endswith('?')

            if is_pain_point or is_low_ratio or is_question:
                pain_posts.append(post)

            if len(pain_posts) >= limit:
                break

        # Normalize
        normalized = []
        for post in pain_posts:
            content = await self.normalize(post)
            # Tag as pain point in metadata
            content.metadata['is_pain_point'] = True
            normalized.append(content)

        return normalized

    async def extract_desires(
        self,
        subreddit: str,
        limit: int = 50
    ) -> list[UnifiedContent]:
        """
        Extract posts with positive sentiment (aspirations / desires)

        Args:
            subreddit: Subreddit to analyze
            limit: Maximum posts

        Returns:
            list[UnifiedContent]: Posts containing desires/aspirations

        Desire indicators:
        - High score and upvote ratio (>0.9)
        - Keywords: "finally", "achieved", "success", "recommend", "best"
        - Sharing accomplishments
        """
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize Reddit client")

        print(f"Mining desires/aspirations from r/{subreddit}...")

        # Get top posts (successful/popular content)
        raw_posts = await self.extract(
            subreddit,
            limit=limit * 2,
            sort="top",
            time_filter="month",
            include_comments=True
        )

        # Filter for desire indicators
        desire_keywords = [
            'finally', 'achieved', 'success', 'recommend', 'best',
            'love', 'amazing', 'life-changing', 'thank you', 'works great',
            'perfect', 'exactly what', 'game changer', 'breakthrough'
        ]

        desire_posts = []
        for post in raw_posts:
            title_lower = post['title'].lower()
            body_lower = post.get('selftext', '').lower()
            combined = title_lower + " " + body_lower

            # Check for desire indicators
            has_desire_keyword = any(keyword in combined for keyword in desire_keywords)
            is_high_ratio = post.get('upvote_ratio', 0) > 0.9
            is_high_score = post.get('score', 0) > 100

            if has_desire_keyword or (is_high_ratio and is_high_score):
                desire_posts.append(post)

            if len(desire_posts) >= limit:
                break

        # Normalize
        normalized = []
        for post in desire_posts:
            content = await self.normalize(post)
            # Tag as desire in metadata
            content.metadata['is_desire_post'] = True
            normalized.append(content)

        return normalized

    async def close(self):
        """Clean up resources"""
        self.client = None
        self._initialized = False
        print("RedditScraper resources cleaned up")

    def __del__(self):
        """Cleanup on deletion"""
        pass  # No persistent connections to close


# Convenience function for quick testing
async def test_reddit_scraper():
    """Test RedditScraper with r/productivity"""
    scraper = RedditScraper()

    print("Initializing RedditScraper...")
    await scraper.initialize()

    print("\nChecking health...")
    health = await scraper.health_check()
    print(f"Health: {health}")

    print("\nScraping 10 hot posts from r/productivity...")
    posts = await scraper.scrape("productivity", limit=10)

    for i, post in enumerate(posts[:5], 1):
        print(f"\n--- Post {i} ---")
        print(f"Platform: {post.platform}")
        print(f"Title: {post.content.title[:80]}...")
        print(f"Author: u/{post.author.username}")
        print(f"Score: {post.metrics.likes}")
        print(f"Comments: {post.metrics.comments}")
        print(f"Upvote Ratio: {post.metadata.get('upvote_ratio', 0):.2%}")
        print(f"Word Count: {post.content.word_count}")
        print(f"URL: {post.source_url}")

    await scraper.close()
    return posts


if __name__ == "__main__":
    asyncio.run(test_reddit_scraper())
```

---

## STEP 3: Update Package Exports

### Update `backend/scrapers/adapters/__init__.py`:

```python
"""
Platform-specific scraper adapters
Each adapter implements the BaseScraper interface
"""

from .twitter import TwitterScraper
from .youtube import YouTubeScraper
from .reddit import RedditScraper

__all__ = ["TwitterScraper", "YouTubeScraper", "RedditScraper"]
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

__all__ = [
    "BaseScraper",
    "UnifiedContent",
    "TwitterScraper",
    "YouTubeScraper",
    "RedditScraper"
]
```

---

## ERROR HANDLING PATTERNS

### PRAW-Specific Errors

```python
from prawcore.exceptions import (
    ResponseException,    # API responded with error
    RequestException,     # Network/connection issue
    TooManyRequests,      # Rate limit exceeded
    NotFound,             # Subreddit doesn't exist
    Forbidden,            # Private/banned subreddit
    ServerError           # Reddit server issue
)

# Handle gracefully
async def safe_extract(self, subreddit: str, limit: int):
    try:
        return await self.extract(subreddit, limit)
    except TooManyRequests as e:
        print(f"Rate limited: {e}")
        # Wait and retry
        await asyncio.sleep(60)
        return await self.extract(subreddit, limit)
    except NotFound:
        print(f"Subreddit r/{subreddit} does not exist")
        return []
    except Forbidden:
        print(f"Subreddit r/{subreddit} is private or banned")
        return []
    except ServerError:
        print("Reddit servers are having issues. Try again later.")
        return []
```

### Deleted Content

```python
# Reddit posts and users can be deleted
def handle_deleted_content(submission):
    author = str(submission.author) if submission.author else '[deleted]'
    body = submission.selftext if submission.selftext != '[deleted]' else ''
    title = submission.title if submission.title != '[deleted]' else 'Deleted Post'

    return {
        'author': author,
        'title': title,
        'body': body
    }
```

### Empty Subreddits

```python
# Handle subreddits with no posts
async def extract_with_fallback(self, subreddit: str, limit: int):
    posts = await self.extract(subreddit, limit)

    if not posts:
        print(f"r/{subreddit} has no posts. Trying alternative sort...")
        posts = await self.extract(subreddit, limit, sort="top", time_filter="all")

    return posts
```

---

## RATE LIMITING STRATEGY

Reddit's FREE OAuth tier is generous:

```python
class RedditRateLimiter:
    """
    Reddit API Rate Limits (OAuth Read-Only):
    - 60 requests per minute
    - 1,000 requests per 10 minutes
    - No strict daily limit

    Strategy:
    - Track requests per window
    - Auto-pause when approaching limits
    - Exponential backoff on errors
    """

    def __init__(self):
        self.requests_per_minute = 0
        self.requests_per_10min = 0
        self.minute_start = datetime.utcnow()
        self.window_start = datetime.utcnow()
        self.max_per_minute = 60
        self.max_per_10min = 1000

    async def wait_if_needed(self):
        now = datetime.utcnow()

        # Reset minute counter
        if (now - self.minute_start).seconds >= 60:
            self.requests_per_minute = 0
            self.minute_start = now

        # Reset 10-minute window
        if (now - self.window_start).seconds >= 600:
            self.requests_per_10min = 0
            self.window_start = now

        # Check minute limit
        if self.requests_per_minute >= self.max_per_minute:
            wait_time = 60 - (now - self.minute_start).seconds
            print(f"Minute rate limit, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)

        # Check 10-minute limit
        if self.requests_per_10min >= self.max_per_10min:
            wait_time = 600 - (now - self.window_start).seconds
            print(f"10-minute rate limit, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)

        # Increment counters
        self.requests_per_minute += 1
        self.requests_per_10min += 1

    def get_remaining(self) -> dict:
        return {
            'minute_remaining': self.max_per_minute - self.requests_per_minute,
            'window_remaining': self.max_per_10min - self.requests_per_10min
        }
```

---

## VOC MINING STRATEGIES

### Pain Point Extraction

```python
# Keywords indicating frustration/problems
PAIN_KEYWORDS = [
    # Direct complaints
    'frustrated', 'hate', 'annoying', 'terrible', 'worst',
    # Problems
    'problem', 'issue', 'bug', 'broken', 'doesn\'t work',
    # Help seeking
    'help', 'advice', 'struggling', 'stuck', 'can\'t figure',
    # Questions
    'how do i', 'why doesn\'t', 'what am i doing wrong'
]

# Sentiment indicators
def is_likely_pain_point(post: dict) -> bool:
    score = 0

    # Check keywords in title/body
    text = f"{post['title']} {post.get('selftext', '')}".lower()
    for keyword in PAIN_KEYWORDS:
        if keyword in text:
            score += 1

    # Low upvote ratio suggests controversial/problematic post
    if post.get('upvote_ratio', 1.0) < 0.7:
        score += 2

    # Questions are often pain points
    if post['title'].endswith('?'):
        score += 1

    return score >= 2
```

### Desire/Success Extraction

```python
# Keywords indicating success/desires
DESIRE_KEYWORDS = [
    # Success
    'finally', 'achieved', 'success', 'breakthrough', 'milestone',
    # Recommendations
    'recommend', 'best', 'must-have', 'game-changer', 'life-changing',
    # Positive emotions
    'love', 'amazing', 'perfect', 'incredible', 'awesome',
    # Sharing wins
    'sharing', 'proud', 'excited', 'happy to report'
]

def is_likely_desire_post(post: dict) -> bool:
    score = 0

    text = f"{post['title']} {post.get('selftext', '')}".lower()
    for keyword in DESIRE_KEYWORDS:
        if keyword in text:
            score += 1

    # High engagement = valuable content
    if post.get('upvote_ratio', 0) > 0.9:
        score += 2

    if post.get('score', 0) > 100:
        score += 1

    return score >= 2
```

---

## SUCCESS CRITERIA

### Functional Requirements
- [ ] Initialize RedditScraper without errors
- [ ] Configure Reddit API credentials (client_id, client_secret)
- [ ] Scrape 50 posts from r/productivity
- [ ] Extract posts with hot, new, top sorting
- [ ] Extract comments with threading preserved
- [ ] Search within subreddits
- [ ] All data normalized to UnifiedContent schema
- [ ] Rate limiting prevents API abuse

### Integration Requirements
- [ ] RedditScraper implements BaseScraper ABC
- [ ] `health_check()` returns proper dict structure
- [ ] `extract()` returns list of raw post dicts
- [ ] `normalize()` returns UnifiedContent Pydantic model
- [ ] `scrape()` combines extract + normalize correctly

### Data Quality
- [ ] Post titles extracted accurately
- [ ] Post bodies (selftext) complete
- [ ] Comments nested correctly with depth
- [ ] Engagement metrics captured (score, upvote_ratio, num_comments)
- [ ] Timestamps parsed correctly (UTC)
- [ ] Author info preserved
- [ ] Subreddit metadata included

### VOC Mining
- [ ] Pain point posts identified correctly
- [ ] Desire/success posts filtered properly
- [ ] Sentiment indicators calculated

### Testing Commands

```bash
# Install dependencies
cd backend
uv pip install praw prawcore ratelimit

# Set environment variables
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
export REDDIT_USER_AGENT="IAC-032-UnifiedScraper/1.0 by u/iamcodio"

# Test basic import
python -c "from backend.scrapers.adapters.reddit import RedditScraper; print('Import OK')"

# Test PRAW client
python -c "
from backend.scrapers.adapters._reddit_client import create_reddit_client
client = create_reddit_client()
print('Client health:', client.get_health_status())
"

# Test hot posts extraction
python -c "
import asyncio
from backend.scrapers.adapters.reddit import test_reddit_scraper
asyncio.run(test_reddit_scraper())
"

# Test 50 posts from r/productivity (SUCCESS CRITERIA)
python -c "
import asyncio
from backend.scrapers.adapters.reddit import RedditScraper

async def test():
    scraper = RedditScraper()
    await scraper.initialize()

    posts = await scraper.scrape('productivity', limit=50)
    print(f'Scraped {len(posts)} posts')

    for i, post in enumerate(posts[:3], 1):
        print(f'{i}. {post.content.title[:60]}')
        print(f'   Score: {post.metrics.likes}, Comments: {post.metrics.comments}')

asyncio.run(test())
"

# Test pain point extraction
python -c "
import asyncio
from backend.scrapers.adapters.reddit import RedditScraper

async def test():
    scraper = RedditScraper()
    await scraper.initialize()

    pain_posts = await scraper.extract_pain_points('productivity', limit=10)
    print(f'Found {len(pain_posts)} pain point posts')

    for post in pain_posts[:3]:
        print(f'- {post.content.title[:60]}')

asyncio.run(test())
"

# Health check
python -c "
import asyncio
from backend.scrapers.adapters.reddit import RedditScraper
async def check():
    s = RedditScraper()
    await s.initialize()
    print(await s.health_check())
asyncio.run(check())
"
```

---

## CRITICAL WARNINGS

1. **UNIQUE USER AGENT IS REQUIRED**: Reddit blocks generic user agents. Use format:
   ```
   <platform>:<app_id>:<version> (by u/<reddit_username>)
   ```

2. **DON'T ABUSE FREE TIER**: 1,000 requests/10min is generous. Don't waste it:
   - Batch requests efficiently
   - Cache results
   - Don't re-scrape same content

3. **RESPECT NSFW/SPOILER FLAGS**: Filter appropriately for your use case.

4. **HANDLE DELETED CONTENT**: Users and posts get deleted. Always check for `[deleted]`.

5. **COMMENT DEPTH IMPACTS PERFORMANCE**: Deep comment trees are slow. Use depth=2 max.

6. **PRIVATE SUBREDDITS EXIST**: Some subreddits are private or quarantined. Handle 403 errors.

7. **REDDIT TOS**: Don't scrape for:
   - Personal data harvesting
   - Spam/marketing automation
   - Bypassing Reddit's content policies

8. **RATE LIMIT RESETS**: The 10-minute window resets after 600 seconds, not rolling window.

---

## ESTIMATED EFFORT

| Task | Time |
|------|------|
| Create Reddit app & get credentials | 10 min |
| Set environment variables | 5 min |
| Write _reddit_client.py | 45 min |
| Write RedditScraper wrapper | 60 min |
| Update package exports | 10 min |
| Install dependencies | 10 min |
| Test initialization | 15 min |
| Test post extraction | 20 min |
| Test comment extraction | 15 min |
| Test VOC mining features | 20 min |
| Verify data quality | 15 min |

**Total: 2-3 hours**

---

## NEXT AGENT (Epsilon)

Once RedditScraper is operational:
- Agent Epsilon: Web Scraper (Jina.ai + ScraperAPI)

---

## SUPPORT CONTACTS

- **Project Lead**: @iamcodio (GitHub)
- **Architecture Docs**: `/Users/kjd/01-projects/IAC-032-unified-scraper/CLAUDE.md`
- **PRAW Documentation**: https://praw.readthedocs.io/

---

**Remember**: Reddit is your best source for authentic Voice of Customer data. Pain points from frustrated users reveal real problems to solve. Success stories reveal what people actually want. This is GOLD for copywriting and course creation.

Good luck, Agent Delta.
