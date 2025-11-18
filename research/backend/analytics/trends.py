"""
Trend Analysis Module

Analyzes topics over time, detects emerging trends, and identifies
cross-platform patterns in the content corpus.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import pandas as pd
from db.connection import DatabaseManager

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes trends in scraped content corpus

    Features:
    - Topic detection over time
    - Trend strength calculation
    - Cross-platform pattern analysis
    - Top sources/authors identification
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def get_topics_over_time(
        self,
        days: int = 30,
        min_frequency: int = 5,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract topics and their frequency over time

        Args:
            days: Number of days to analyze
            min_frequency: Minimum word frequency to include
            platform: Optional platform filter

        Returns:
            Dict with timeline data and top topics
        """
        logger.info(f"Analyzing topics over time: days={days}, platform={platform}")

        # Build query
        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)

        query = f"""
            SELECT
                s.platform,
                DATE_TRUNC('day', s.scraped_at) as date,
                c.text_content,
                c.word_count,
                s.author,
                s.published_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            {where_clause}
            ORDER BY s.scraped_at DESC
        """

        rows = await self.db.fetch(query, *params)

        if not rows:
            return {
                "timeline": [],
                "top_topics": [],
                "total_content": 0
            }

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([dict(row) for row in rows])

        # Extract words and count by date
        topic_timeline = defaultdict(lambda: Counter())

        for _, row in df.iterrows():
            date = row['date'].date()
            words = self._extract_keywords(row['text_content'])
            topic_timeline[date].update(words)

        # Build timeline data
        timeline = []
        all_words = Counter()

        for date in sorted(topic_timeline.keys()):
            word_counts = topic_timeline[date]
            all_words.update(word_counts)

            top_words = word_counts.most_common(10)
            timeline.append({
                "date": date.isoformat(),
                "top_topics": [
                    {"word": word, "count": count}
                    for word, count in top_words
                ],
                "content_count": len([w for w in word_counts.values()])
            })

        # Get overall top topics
        top_topics = [
            {"word": word, "count": count, "trend": "stable"}
            for word, count in all_words.most_common(50)
            if count >= min_frequency
        ]

        # Calculate trend direction (simple momentum)
        recent_words = Counter()
        older_words = Counter()
        midpoint = datetime.now().date() - timedelta(days=days // 2)

        for date, words in topic_timeline.items():
            if date >= midpoint:
                recent_words.update(words)
            else:
                older_words.update(words)

        # Update trend indicators
        for topic in top_topics:
            word = topic['word']
            recent_count = recent_words.get(word, 0)
            older_count = older_words.get(word, 1)  # Avoid division by zero

            ratio = recent_count / older_count if older_count > 0 else float('inf')

            if ratio > 1.5:
                topic['trend'] = 'rising'
            elif ratio < 0.67:
                topic['trend'] = 'declining'
            else:
                topic['trend'] = 'stable'

        logger.info(f"Analyzed {len(rows)} content pieces, found {len(top_topics)} topics")

        return {
            "timeline": timeline,
            "top_topics": top_topics,
            "total_content": len(rows),
            "date_range": {
                "start": min(topic_timeline.keys()).isoformat(),
                "end": max(topic_timeline.keys()).isoformat()
            }
        }

    async def detect_cross_platform_patterns(
        self,
        min_platforms: int = 2,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Identify topics that appear across multiple platforms

        Args:
            min_platforms: Minimum number of platforms for a pattern
            days: Time window to analyze

        Returns:
            List of cross-platform patterns
        """
        logger.info(f"Detecting cross-platform patterns: min_platforms={min_platforms}")

        query = """
            SELECT
                s.platform,
                c.text_content,
                s.author,
                s.published_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval
            ORDER BY s.scraped_at DESC
        """

        rows = await self.db.fetch(query, f"{days} days")

        if not rows:
            return []

        # Group content by platform
        platform_words = defaultdict(Counter)

        for row in rows:
            platform = row['platform']
            words = self._extract_keywords(row['text_content'])
            platform_words[platform].update(words)

        # Find words that appear in multiple platforms
        word_platforms = defaultdict(set)

        for platform, word_counts in platform_words.items():
            for word in word_counts.keys():
                word_platforms[word].add(platform)

        # Filter for cross-platform patterns
        patterns = []

        for word, platforms in word_platforms.items():
            if len(platforms) >= min_platforms:
                total_count = sum(
                    platform_words[p].get(word, 0)
                    for p in platforms
                )

                patterns.append({
                    "topic": word,
                    "platforms": sorted(list(platforms)),
                    "platform_count": len(platforms),
                    "total_mentions": total_count,
                    "distribution": {
                        p: platform_words[p].get(word, 0)
                        for p in platforms
                    }
                })

        # Sort by number of platforms and total mentions
        patterns.sort(
            key=lambda x: (x['platform_count'], x['total_mentions']),
            reverse=True
        )

        logger.info(f"Found {len(patterns)} cross-platform patterns")

        return patterns[:100]  # Return top 100

    async def get_top_authors(
        self,
        days: int = 30,
        limit: int = 20,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top content authors/sources by activity and engagement

        Args:
            days: Time window
            limit: Number of authors to return
            platform: Optional platform filter

        Returns:
            List of top authors with statistics
        """
        logger.info(f"Getting top authors: days={days}, platform={platform}")

        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)
            params.append(limit)
        else:
            params.append(limit)

        query = f"""
            SELECT
                s.author,
                s.platform,
                COUNT(DISTINCT s.id) as source_count,
                COUNT(c.id) as content_count,
                AVG(c.word_count)::integer as avg_word_count,
                MAX(s.scraped_at) as last_scraped
            FROM sources s
            LEFT JOIN contents c ON s.id = c.source_id
            {where_clause}
            AND s.author IS NOT NULL
            GROUP BY s.author, s.platform
            ORDER BY content_count DESC, source_count DESC
            LIMIT ${len(params)}
        """

        rows = await self.db.fetch(query, *params)

        authors = []
        for row in rows:
            authors.append({
                "author": row['author'],
                "platform": row['platform'],
                "source_count": row['source_count'],
                "content_count": row['content_count'],
                "avg_word_count": row['avg_word_count'],
                "last_scraped": row['last_scraped'].isoformat() if row['last_scraped'] else None
            })

        logger.info(f"Found {len(authors)} top authors")

        return authors

    async def get_platform_statistics(self) -> List[Dict[str, Any]]:
        """
        Get comprehensive statistics by platform

        Returns:
            List of platform statistics
        """
        logger.info("Getting platform statistics")

        query = """
            SELECT
                s.platform,
                COUNT(DISTINCT s.id) as source_count,
                COUNT(c.id) as content_count,
                AVG(c.word_count)::integer as avg_word_count,
                SUM(c.word_count) as total_words,
                MIN(s.scraped_at) as first_scraped,
                MAX(s.scraped_at) as last_scraped,
                COUNT(DISTINCT s.author) as unique_authors
            FROM sources s
            LEFT JOIN contents c ON s.id = c.source_id
            GROUP BY s.platform
            ORDER BY content_count DESC
        """

        rows = await self.db.fetch(query)

        stats = []
        for row in rows:
            stats.append({
                "platform": row['platform'],
                "source_count": row['source_count'],
                "content_count": row['content_count'],
                "avg_word_count": row['avg_word_count'],
                "total_words": row['total_words'],
                "first_scraped": row['first_scraped'].isoformat() if row['first_scraped'] else None,
                "last_scraped": row['last_scraped'].isoformat() if row['last_scraped'] else None,
                "unique_authors": row['unique_authors']
            })

        logger.info(f"Retrieved statistics for {len(stats)} platforms")

        return stats

    def _extract_keywords(self, text: str, min_length: int = 4) -> List[str]:
        """
        Extract keywords from text (simple implementation)

        Args:
            text: Input text
            min_length: Minimum word length

        Returns:
            List of keywords
        """
        # Simple keyword extraction - lowercase, filter stopwords, min length
        stopwords = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
            'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
            'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
            'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
            'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
            'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
            'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
            'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
            'give', 'day', 'most', 'us', 'is', 'was', 'are', 'been', 'has',
            'had', 'were', 'said', 'did', 'having', 'may', 'should', 'am'
        }

        words = text.lower().split()
        keywords = [
            word.strip('.,!?;:()[]{}"\'-')
            for word in words
            if len(word) >= min_length and word.lower() not in stopwords
        ]

        return keywords

    async def get_word_frequency(
        self,
        days: int = 30,
        limit: int = 100,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get word frequency data for word cloud generation

        Args:
            days: Time window
            limit: Number of words to return
            platform: Optional platform filter

        Returns:
            List of words with frequencies
        """
        logger.info(f"Getting word frequency: days={days}, limit={limit}")

        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)

        query = f"""
            SELECT
                c.text_content
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            {where_clause}
        """

        rows = await self.db.fetch(query, *params)

        # Count all words
        word_counter = Counter()

        for row in rows:
            words = self._extract_keywords(row['text_content'])
            word_counter.update(words)

        # Return top words
        word_freq = [
            {"word": word, "frequency": count}
            for word, count in word_counter.most_common(limit)
        ]

        logger.info(f"Analyzed {len(rows)} content pieces, found {len(word_freq)} top words")

        return word_freq
