"""
Database module for Research Backend

Provides PostgreSQL connection pooling and database utilities.
"""

from .connection import DatabaseManager, get_db_manager
from .crud import ContentCRUD, SourceCRUD, ScrapeJobCRUD
from .search import VectorSearch

__all__ = [
    "DatabaseManager",
    "get_db_manager",
    "ContentCRUD",
    "SourceCRUD",
    "ScrapeJobCRUD",
    "VectorSearch",
]
