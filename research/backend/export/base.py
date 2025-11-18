"""
Base Exporter Class

Provides shared functionality for all export formats.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from ..db import DatabaseManager, SourceCRUD, ContentCRUD

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for all exporters"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize exporter

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self.source_crud = SourceCRUD(db_manager)
        self.content_crud = ContentCRUD(db_manager)

    async def fetch_corpus_data(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch corpus data from database

        Args:
            platform: Filter by platform (twitter, youtube, reddit, web)
            limit: Maximum number of records to fetch
            source_ids: Specific source IDs to export

        Returns:
            List of records with source and content data
        """
        logger.info(f"Fetching corpus data: platform={platform}, limit={limit}")

        # Build query based on filters
        query_parts = []
        params = []
        param_idx = 1

        query = """
            SELECT
                s.id as source_id,
                s.platform,
                s.url,
                s.title,
                s.author,
                s.published_at,
                s.scraped_at,
                s.metadata as source_metadata,
                c.id as content_id,
                c.content_type,
                c.text_content,
                c.word_count,
                c.language,
                c.metadata as content_metadata,
                c.created_at as content_created_at
            FROM sources s
            LEFT JOIN contents c ON s.id = c.source_id
            WHERE 1=1
        """

        if platform:
            query_parts.append(f"AND s.platform = ${param_idx}")
            params.append(platform)
            param_idx += 1

        if source_ids:
            placeholders = ','.join([f'${i}' for i in range(param_idx, param_idx + len(source_ids))])
            query_parts.append(f"AND s.id IN ({placeholders})")
            params.extend(source_ids)
            param_idx += len(source_ids)

        query += ' '.join(query_parts)
        query += " ORDER BY s.scraped_at DESC, c.created_at DESC"

        if limit:
            query += f" LIMIT ${param_idx}"
            params.append(limit)

        rows = await self.db.fetch(query, *params)

        # Convert to dict and group by source
        records = {}
        for row in rows:
            source_id = str(row['source_id'])

            if source_id not in records:
                records[source_id] = {
                    'source_id': source_id,
                    'platform': row['platform'],
                    'url': row['url'],
                    'title': row['title'],
                    'author': row['author'],
                    'published_at': row['published_at'],
                    'scraped_at': row['scraped_at'],
                    'source_metadata': row['source_metadata'],
                    'contents': []
                }

            # Add content if present
            if row['content_id']:
                records[source_id]['contents'].append({
                    'content_id': str(row['content_id']),
                    'content_type': row['content_type'],
                    'text_content': row['text_content'],
                    'word_count': row['word_count'],
                    'language': row['language'],
                    'content_metadata': row['content_metadata'],
                    'created_at': row['content_created_at']
                })

        result = list(records.values())
        logger.info(f"Fetched {len(result)} sources with content")
        return result

    @abstractmethod
    async def export(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus data to specific format

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs to export

        Returns:
            Formatted export string
        """
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """Return the MIME content type for this export format"""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return the file extension for this export format"""
        pass
