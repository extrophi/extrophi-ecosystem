"""
Analytics API Routes

Provides endpoints for corpus analytics including:
- Trend detection over time
- Sentiment analysis
- Cross-platform pattern analysis
- Word clouds and frequency data
- Top authors and sources
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from analytics import TrendAnalyzer, SentimentAnalyzer
from db import get_db_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


# ============================================================================
# Response Models
# ============================================================================

class TopicItem(BaseModel):
    """Single topic with frequency"""
    word: str
    count: int
    trend: Optional[str] = None  # rising, stable, declining


class TimelineItem(BaseModel):
    """Daily topic data"""
    date: str
    top_topics: List[TopicItem]
    content_count: int


class TrendsResponse(BaseModel):
    """Topics over time response"""
    timeline: List[TimelineItem]
    top_topics: List[TopicItem]
    total_content: int
    date_range: Optional[Dict[str, str]] = None


class CrossPlatformPattern(BaseModel):
    """Cross-platform pattern"""
    topic: str
    platforms: List[str]
    platform_count: int
    total_mentions: int
    distribution: Dict[str, int]


class AuthorStats(BaseModel):
    """Author statistics"""
    author: str
    platform: str
    source_count: int
    content_count: int
    avg_word_count: int
    last_scraped: Optional[str]


class PlatformStats(BaseModel):
    """Platform statistics"""
    platform: str
    source_count: int
    content_count: int
    avg_word_count: int
    total_words: int
    first_scraped: Optional[str]
    last_scraped: Optional[str]
    unique_authors: int


class WordFrequency(BaseModel):
    """Word frequency for word cloud"""
    word: str
    frequency: int


class SentimentOverall(BaseModel):
    """Overall sentiment counts"""
    positive: int
    negative: int
    neutral: int


class SentimentPercentages(BaseModel):
    """Sentiment percentages"""
    positive: float
    negative: float
    neutral: float


class CorpusSentimentResponse(BaseModel):
    """Corpus sentiment analysis response"""
    overall: SentimentOverall
    percentages: SentimentPercentages
    average_compound: float
    overall_sentiment: str  # positive, negative, neutral
    total_analyzed: int


class SentimentTimelineItem(BaseModel):
    """Daily sentiment data"""
    date: str
    positive: int
    negative: int
    neutral: int
    total: int
    average_compound: float


class PlatformSentiment(BaseModel):
    """Platform sentiment statistics"""
    platform: str
    positive: int
    negative: int
    neutral: int
    total: int
    percentages: SentimentPercentages
    average_compound: float


class AuthorSentiment(BaseModel):
    """Author sentiment statistics"""
    author: str
    platform: str
    positive: int
    negative: int
    neutral: int
    total_content: int
    average_compound: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/trends/topics", response_model=TrendsResponse)
async def get_topics_over_time(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_frequency: int = Query(5, ge=1, le=100, description="Minimum word frequency"),
    platform: Optional[str] = Query(None, description="Optional platform filter")
):
    """
    Get topics and trends over time

    Analyzes content to detect trending topics, their frequency over time,
    and whether they are rising, stable, or declining.

    - **days**: Time window (1-365 days)
    - **min_frequency**: Minimum word frequency to include (1-100)
    - **platform**: Optional platform filter (twitter, youtube, reddit, web)
    """
    logger.info(f"GET /analytics/trends/topics: days={days}, platform={platform}")

    try:
        db_manager = get_db_manager()
        analyzer = TrendAnalyzer(db_manager)

        result = await analyzer.get_topics_over_time(
            days=days,
            min_frequency=min_frequency,
            platform=platform
        )

        return result

    except Exception as e:
        logger.error(f"Error getting topics over time: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze topics: {str(e)}"
        )


@router.get("/trends/cross-platform", response_model=List[CrossPlatformPattern])
async def get_cross_platform_patterns(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_platforms: int = Query(2, ge=2, le=10, description="Minimum platforms for a pattern")
):
    """
    Detect cross-platform patterns

    Identifies topics that appear across multiple platforms, indicating
    cross-platform themes and elaboration patterns.

    - **days**: Time window (1-365 days)
    - **min_platforms**: Minimum number of platforms (2-10)
    """
    logger.info(f"GET /analytics/trends/cross-platform: days={days}, min_platforms={min_platforms}")

    try:
        db_manager = get_db_manager()
        analyzer = TrendAnalyzer(db_manager)

        patterns = await analyzer.detect_cross_platform_patterns(
            min_platforms=min_platforms,
            days=days
        )

        return patterns

    except Exception as e:
        logger.error(f"Error detecting cross-platform patterns: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect patterns: {str(e)}"
        )


@router.get("/trends/authors", response_model=List[AuthorStats])
async def get_top_authors(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Number of authors to return"),
    platform: Optional[str] = Query(None, description="Optional platform filter")
):
    """
    Get top content authors/sources

    Returns the most active authors ranked by content volume and activity.

    - **days**: Time window (1-365 days)
    - **limit**: Number of authors to return (1-100)
    - **platform**: Optional platform filter
    """
    logger.info(f"GET /analytics/trends/authors: days={days}, limit={limit}")

    try:
        db_manager = get_db_manager()
        analyzer = TrendAnalyzer(db_manager)

        authors = await analyzer.get_top_authors(
            days=days,
            limit=limit,
            platform=platform
        )

        return authors

    except Exception as e:
        logger.error(f"Error getting top authors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get authors: {str(e)}"
        )


@router.get("/trends/platforms", response_model=List[PlatformStats])
async def get_platform_statistics():
    """
    Get comprehensive platform statistics

    Returns detailed statistics for each platform including content counts,
    word counts, date ranges, and unique authors.
    """
    logger.info("GET /analytics/trends/platforms")

    try:
        db_manager = get_db_manager()
        analyzer = TrendAnalyzer(db_manager)

        stats = await analyzer.get_platform_statistics()

        return stats

    except Exception as e:
        logger.error(f"Error getting platform statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform stats: {str(e)}"
        )


@router.get("/trends/wordcloud", response_model=List[WordFrequency])
async def get_word_frequency(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(100, ge=10, le=500, description="Number of words to return"),
    platform: Optional[str] = Query(None, description="Optional platform filter")
):
    """
    Get word frequency data for word cloud

    Returns the most frequently used words in the corpus, suitable for
    generating word cloud visualizations.

    - **days**: Time window (1-365 days)
    - **limit**: Number of words to return (10-500)
    - **platform**: Optional platform filter
    """
    logger.info(f"GET /analytics/trends/wordcloud: days={days}, limit={limit}")

    try:
        db_manager = get_db_manager()
        analyzer = TrendAnalyzer(db_manager)

        word_freq = await analyzer.get_word_frequency(
            days=days,
            limit=limit,
            platform=platform
        )

        return word_freq

    except Exception as e:
        logger.error(f"Error getting word frequency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get word frequency: {str(e)}"
        )


@router.get("/sentiment/corpus", response_model=CorpusSentimentResponse)
async def analyze_corpus_sentiment(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    platform: Optional[str] = Query(None, description="Optional platform filter"),
    limit: Optional[int] = Query(None, ge=10, le=10000, description="Optional content limit")
):
    """
    Analyze overall corpus sentiment

    Provides aggregate sentiment statistics across the entire content corpus
    or filtered by platform.

    - **days**: Time window (1-365 days)
    - **platform**: Optional platform filter
    - **limit**: Optional limit on content to analyze (for performance)
    """
    logger.info(f"GET /analytics/sentiment/corpus: days={days}, platform={platform}")

    try:
        db_manager = get_db_manager()
        analyzer = SentimentAnalyzer(db_manager)

        result = await analyzer.analyze_corpus(
            days=days,
            platform=platform,
            limit=limit
        )

        return result

    except Exception as e:
        logger.error(f"Error analyzing corpus sentiment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiment: {str(e)}"
        )


@router.get("/sentiment/timeline", response_model=List[SentimentTimelineItem])
async def get_sentiment_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    platform: Optional[str] = Query(None, description="Optional platform filter")
):
    """
    Get sentiment trends over time

    Shows how sentiment changes day by day, useful for identifying
    sentiment shifts and trends.

    - **days**: Time window (1-365 days)
    - **platform**: Optional platform filter
    """
    logger.info(f"GET /analytics/sentiment/timeline: days={days}, platform={platform}")

    try:
        db_manager = get_db_manager()
        analyzer = SentimentAnalyzer(db_manager)

        timeline = await analyzer.sentiment_over_time(
            days=days,
            platform=platform
        )

        return timeline

    except Exception as e:
        logger.error(f"Error getting sentiment timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sentiment timeline: {str(e)}"
        )


@router.get("/sentiment/platforms", response_model=List[PlatformSentiment])
async def get_sentiment_by_platform(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Compare sentiment across platforms

    Shows sentiment distribution for each platform, allowing comparison
    of sentiment patterns across different content sources.

    - **days**: Time window (1-365 days)
    """
    logger.info(f"GET /analytics/sentiment/platforms: days={days}")

    try:
        db_manager = get_db_manager()
        analyzer = SentimentAnalyzer(db_manager)

        results = await analyzer.sentiment_by_platform(days=days)

        return results

    except Exception as e:
        logger.error(f"Error getting sentiment by platform: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform sentiment: {str(e)}"
        )


@router.get("/sentiment/authors", response_model=List[AuthorSentiment])
async def get_sentiment_by_author(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Number of authors to return"),
    platform: Optional[str] = Query(None, description="Optional platform filter")
):
    """
    Analyze sentiment by author

    Shows sentiment patterns for the most active authors, identifying
    consistently positive or negative content creators.

    - **days**: Time window (1-365 days)
    - **limit**: Number of authors to return (1-100)
    - **platform**: Optional platform filter
    """
    logger.info(f"GET /analytics/sentiment/authors: days={days}, limit={limit}")

    try:
        db_manager = get_db_manager()
        analyzer = SentimentAnalyzer(db_manager)

        results = await analyzer.sentiment_by_author(
            days=days,
            limit=limit,
            platform=platform
        )

        return results

    except Exception as e:
        logger.error(f"Error getting sentiment by author: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get author sentiment: {str(e)}"
        )
