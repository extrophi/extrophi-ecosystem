"""
Analytics Module

Provides corpus analytics including trend detection, sentiment analysis,
pattern recognition, and insights generation.
"""

from .trends import TrendAnalyzer
from .sentiment import SentimentAnalyzer

__all__ = ["TrendAnalyzer", "SentimentAnalyzer"]
