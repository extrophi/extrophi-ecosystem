"""
Sentiment Analysis Module

Analyzes sentiment of scraped content using VADER sentiment analysis.
VADER is specifically tuned for social media and works well without training.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("vaderSentiment not installed. Sentiment analysis will use fallback method.")

from db.connection import DatabaseManager

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzes sentiment of content corpus

    Features:
    - Positive/negative/neutral classification
    - Sentiment trends over time
    - Platform-specific sentiment comparison
    - Author sentiment patterns
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

        if VADER_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("Using VADER sentiment analyzer")
        else:
            self.analyzer = None
            logger.warning("VADER not available, using basic sentiment analysis")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text

        Args:
            text: Input text

        Returns:
            Dict with sentiment scores and classification
        """
        if self.analyzer:
            # Use VADER
            scores = self.analyzer.polarity_scores(text)

            # Classify based on compound score
            compound = scores['compound']
            if compound >= 0.05:
                sentiment = 'positive'
            elif compound <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'sentiment': sentiment,
                'scores': {
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'compound': scores['compound']
                }
            }
        else:
            # Fallback: Simple keyword-based sentiment
            return self._basic_sentiment(text)

    def _basic_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Basic sentiment analysis using keyword matching

        Args:
            text: Input text

        Returns:
            Dict with sentiment classification and basic scores
        """
        text_lower = text.lower()

        # Simple positive/negative word lists
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'awesome', 'best', 'love', 'happy', 'joy', 'success', 'win',
            'brilliant', 'perfect', 'beautiful', 'incredible', 'outstanding'
        }

        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'sad',
            'fail', 'failure', 'poor', 'disappointing', 'wrong', 'problem',
            'issue', 'difficult', 'hard', 'struggle', 'unfortunately'
        }

        words = text_lower.split()
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)

        total = pos_count + neg_count
        if total == 0:
            sentiment = 'neutral'
            pos_score = 0.0
            neg_score = 0.0
        else:
            pos_score = pos_count / total
            neg_score = neg_count / total

            if pos_count > neg_count:
                sentiment = 'positive'
            elif neg_count > pos_count:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

        return {
            'sentiment': sentiment,
            'scores': {
                'positive': pos_score,
                'negative': neg_score,
                'neutral': 1.0 - (pos_score + neg_score),
                'compound': pos_score - neg_score
            }
        }

    async def analyze_corpus(
        self,
        days: int = 30,
        platform: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment across entire corpus

        Args:
            days: Time window to analyze
            platform: Optional platform filter
            limit: Optional limit on content to analyze

        Returns:
            Dict with aggregate sentiment statistics
        """
        logger.info(f"Analyzing corpus sentiment: days={days}, platform={platform}")

        # Build query
        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)

        limit_clause = f"LIMIT {limit}" if limit else ""

        query = f"""
            SELECT
                c.id,
                c.text_content,
                s.platform,
                s.author,
                s.scraped_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            {where_clause}
            ORDER BY s.scraped_at DESC
            {limit_clause}
        """

        rows = await self.db.fetch(query, *params)

        if not rows:
            return {
                "overall": {"positive": 0, "negative": 0, "neutral": 0},
                "total_analyzed": 0
            }

        # Analyze each piece of content
        sentiment_counts = Counter()
        sentiment_scores = []

        for row in rows:
            result = self.analyze_text(row['text_content'])
            sentiment_counts[result['sentiment']] += 1
            sentiment_scores.append(result['scores']['compound'])

        total = len(rows)

        # Calculate statistics
        avg_compound = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        overall_sentiment = 'neutral'
        if avg_compound >= 0.05:
            overall_sentiment = 'positive'
        elif avg_compound <= -0.05:
            overall_sentiment = 'negative'

        logger.info(f"Analyzed {total} content pieces: {dict(sentiment_counts)}")

        return {
            "overall": {
                "positive": sentiment_counts.get('positive', 0),
                "negative": sentiment_counts.get('negative', 0),
                "neutral": sentiment_counts.get('neutral', 0)
            },
            "percentages": {
                "positive": round(sentiment_counts.get('positive', 0) / total * 100, 2) if total > 0 else 0,
                "negative": round(sentiment_counts.get('negative', 0) / total * 100, 2) if total > 0 else 0,
                "neutral": round(sentiment_counts.get('neutral', 0) / total * 100, 2) if total > 0 else 0
            },
            "average_compound": round(avg_compound, 3),
            "overall_sentiment": overall_sentiment,
            "total_analyzed": total
        }

    async def sentiment_over_time(
        self,
        days: int = 30,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment trends over time

        Args:
            days: Time window
            platform: Optional platform filter

        Returns:
            List of daily sentiment data
        """
        logger.info(f"Analyzing sentiment over time: days={days}")

        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)

        query = f"""
            SELECT
                DATE_TRUNC('day', s.scraped_at) as date,
                c.text_content,
                s.platform
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            {where_clause}
            ORDER BY date DESC
        """

        rows = await self.db.fetch(query, *params)

        if not rows:
            return []

        # Group by date and analyze
        from collections import defaultdict
        date_content = defaultdict(list)

        for row in rows:
            date = row['date'].date()
            date_content[date].append(row['text_content'])

        # Analyze each day
        timeline = []

        for date in sorted(date_content.keys()):
            content_list = date_content[date]
            sentiment_counts = Counter()
            compound_scores = []

            for text in content_list:
                result = self.analyze_text(text)
                sentiment_counts[result['sentiment']] += 1
                compound_scores.append(result['scores']['compound'])

            total = len(content_list)
            avg_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0.0

            timeline.append({
                "date": date.isoformat(),
                "positive": sentiment_counts.get('positive', 0),
                "negative": sentiment_counts.get('negative', 0),
                "neutral": sentiment_counts.get('neutral', 0),
                "total": total,
                "average_compound": round(avg_compound, 3)
            })

        logger.info(f"Analyzed sentiment for {len(timeline)} days")

        return timeline

    async def sentiment_by_platform(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Compare sentiment across platforms

        Args:
            days: Time window

        Returns:
            List of platform sentiment statistics
        """
        logger.info(f"Analyzing sentiment by platform: days={days}")

        query = """
            SELECT
                s.platform,
                c.text_content
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval
            ORDER BY s.platform
        """

        rows = await self.db.fetch(query, f"{days} days")

        if not rows:
            return []

        # Group by platform
        from collections import defaultdict
        platform_content = defaultdict(list)

        for row in rows:
            platform_content[row['platform']].append(row['text_content'])

        # Analyze each platform
        results = []

        for platform, content_list in platform_content.items():
            sentiment_counts = Counter()
            compound_scores = []

            for text in content_list:
                result = self.analyze_text(text)
                sentiment_counts[result['sentiment']] += 1
                compound_scores.append(result['scores']['compound'])

            total = len(content_list)
            avg_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0.0

            results.append({
                "platform": platform,
                "positive": sentiment_counts.get('positive', 0),
                "negative": sentiment_counts.get('negative', 0),
                "neutral": sentiment_counts.get('neutral', 0),
                "total": total,
                "percentages": {
                    "positive": round(sentiment_counts.get('positive', 0) / total * 100, 2) if total > 0 else 0,
                    "negative": round(sentiment_counts.get('negative', 0) / total * 100, 2) if total > 0 else 0,
                    "neutral": round(sentiment_counts.get('neutral', 0) / total * 100, 2) if total > 0 else 0
                },
                "average_compound": round(avg_compound, 3)
            })

        # Sort by total content
        results.sort(key=lambda x: x['total'], reverse=True)

        logger.info(f"Analyzed sentiment for {len(results)} platforms")

        return results

    async def sentiment_by_author(
        self,
        days: int = 30,
        limit: int = 20,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment by author

        Args:
            days: Time window
            limit: Number of authors to return
            platform: Optional platform filter

        Returns:
            List of author sentiment statistics
        """
        logger.info(f"Analyzing sentiment by author: days={days}, limit={limit}")

        where_clause = "WHERE s.scraped_at >= CURRENT_TIMESTAMP - $1::interval AND s.author IS NOT NULL"
        params = [f"{days} days"]

        if platform:
            where_clause += " AND s.platform = $2"
            params.append(platform)

        query = f"""
            SELECT
                s.author,
                s.platform,
                c.text_content
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            {where_clause}
            ORDER BY s.author
        """

        rows = await self.db.fetch(query, *params)

        if not rows:
            return []

        # Group by author
        from collections import defaultdict
        author_content = defaultdict(list)

        for row in rows:
            key = (row['author'], row['platform'])
            author_content[key].append(row['text_content'])

        # Analyze each author
        results = []

        for (author, platform), content_list in author_content.items():
            sentiment_counts = Counter()
            compound_scores = []

            for text in content_list:
                result = self.analyze_text(text)
                sentiment_counts[result['sentiment']] += 1
                compound_scores.append(result['scores']['compound'])

            total = len(content_list)
            avg_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0.0

            results.append({
                "author": author,
                "platform": platform,
                "positive": sentiment_counts.get('positive', 0),
                "negative": sentiment_counts.get('negative', 0),
                "neutral": sentiment_counts.get('neutral', 0),
                "total_content": total,
                "average_compound": round(avg_compound, 3)
            })

        # Sort by total content and return top N
        results.sort(key=lambda x: x['total_content'], reverse=True)

        logger.info(f"Analyzed sentiment for {len(results)} authors")

        return results[:limit]
