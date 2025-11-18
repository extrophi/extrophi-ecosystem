"""
API Routes Module

Contains all API route handlers.
"""

from .analytics import router as analytics_router

__all__ = ["analytics_router"]
