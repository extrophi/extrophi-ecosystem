"""
Tests for analytics module

Tests trend analysis, sentiment analysis, and analytics API endpoints.
"""

import pytest
from collections import Counter

from analytics import TrendAnalyzer, SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""

    def test_basic_sentiment_positive(self):
        """Test positive sentiment detection"""
        analyzer = SentimentAnalyzer(db_manager=None)

        result = analyzer._basic_sentiment("This is great! I love it. Wonderful and amazing.")

        assert result['sentiment'] == 'positive'
        assert result['scores']['positive'] > 0
        assert result['scores']['compound'] > 0

    def test_basic_sentiment_negative(self):
        """Test negative sentiment detection"""
        analyzer = SentimentAnalyzer(db_manager=None)

        result = analyzer._basic_sentiment("This is terrible. I hate it. Awful and horrible.")

        assert result['sentiment'] == 'negative'
        assert result['scores']['negative'] > 0
        assert result['scores']['compound'] < 0

    def test_basic_sentiment_neutral(self):
        """Test neutral sentiment detection"""
        analyzer = SentimentAnalyzer(db_manager=None)

        result = analyzer._basic_sentiment("The meeting is scheduled for tomorrow at 2pm.")

        assert result['sentiment'] == 'neutral'

    def test_analyze_text_with_vader(self):
        """Test sentiment analysis with VADER if available"""
        analyzer = SentimentAnalyzer(db_manager=None)

        result = analyzer.analyze_text("I absolutely love this! It's amazing and wonderful!")

        assert 'sentiment' in result
        assert 'scores' in result
        assert result['sentiment'] in ['positive', 'negative', 'neutral']
        assert 'compound' in result['scores']


class TestTrendAnalyzer:
    """Test trend analysis functionality"""

    def test_extract_keywords(self):
        """Test keyword extraction"""
        analyzer = TrendAnalyzer(db_manager=None)

        text = "Machine learning and artificial intelligence are transforming technology"
        keywords = analyzer._extract_keywords(text, min_length=4)

        assert 'machine' in keywords
        assert 'learning' in keywords
        assert 'artificial' in keywords
        assert 'intelligence' in keywords
        assert 'transforming' in keywords
        assert 'technology' in keywords

        # Stopwords should be filtered
        assert 'and' not in keywords
        assert 'are' not in keywords

    def test_extract_keywords_min_length(self):
        """Test keyword extraction with minimum length filter"""
        analyzer = TrendAnalyzer(db_manager=None)

        text = "AI ML and deep learning"
        keywords = analyzer._extract_keywords(text, min_length=5)

        assert 'learning' in keywords
        # Short words should be filtered
        assert 'deep' not in keywords


@pytest.mark.asyncio
async def test_analytics_endpoints_structure():
    """Test that analytics router is properly structured"""
    from api.routes.analytics import router

    # Verify router exists
    assert router is not None
    assert router.prefix == "/api/analytics"

    # Verify routes are registered
    route_paths = [route.path for route in router.routes]

    expected_routes = [
        "/api/analytics/trends/topics",
        "/api/analytics/trends/cross-platform",
        "/api/analytics/trends/authors",
        "/api/analytics/trends/platforms",
        "/api/analytics/trends/wordcloud",
        "/api/analytics/sentiment/corpus",
        "/api/analytics/sentiment/timeline",
        "/api/analytics/sentiment/platforms",
        "/api/analytics/sentiment/authors",
    ]

    for expected_route in expected_routes:
        assert expected_route in route_paths, f"Route {expected_route} not found"


def test_sentiment_analyzer_initialization():
    """Test SentimentAnalyzer initialization"""
    analyzer = SentimentAnalyzer(db_manager=None)

    assert analyzer is not None
    assert analyzer.db is None  # No db_manager provided


def test_trend_analyzer_initialization():
    """Test TrendAnalyzer initialization"""
    analyzer = TrendAnalyzer(db_manager=None)

    assert analyzer is not None
    assert analyzer.db is None  # No db_manager provided
