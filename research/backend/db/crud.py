"""
CRUD operations for Research Backend database

Provides Create, Read, Update, Delete operations for:
- Sources (content sources)
- Contents (scraped content with embeddings)
- Scrape Jobs (async job tracking)
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from .connection import DatabaseManager

logger = logging.getLogger(__name__)


class SourceCRUD:
    """CRUD operations for sources table"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create(
        self,
        platform: str,
        url: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        published_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Create new source

        Args:
            platform: Platform name (twitter, youtube, reddit, web)
            url: Source URL (must be unique)
            title: Content title
            author: Content author
            published_at: Publication timestamp
            metadata: Platform-specific metadata

        Returns:
            Source UUID
        """
        query = """
            INSERT INTO sources (platform, url, title, author, published_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """

        source_id = await self.db.fetchval(
            query,
            platform,
            url,
            title,
            author,
            published_at,
            metadata or {}
        )

        logger.info(f"Created source: {source_id} ({platform} - {url})")
        return source_id

    async def get_by_id(self, source_id: UUID) -> Optional[Dict[str, Any]]:
        """Get source by ID"""
        query = "SELECT * FROM sources WHERE id = $1"
        row = await self.db.fetchrow(query, source_id)
        return dict(row) if row else None

    async def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get source by URL"""
        query = "SELECT * FROM sources WHERE url = $1"
        row = await self.db.fetchrow(query, url)
        return dict(row) if row else None

    async def list_by_platform(
        self,
        platform: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List sources by platform"""
        query = """
            SELECT * FROM sources
            WHERE platform = $1
            ORDER BY scraped_at DESC
            LIMIT $2 OFFSET $3
        """
        rows = await self.db.fetch(query, platform, limit, offset)
        return [dict(row) for row in rows]

    async def update(
        self,
        source_id: UUID,
        title: Optional[str] = None,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update source"""
        updates = []
        params = []
        param_idx = 1

        if title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(title)
            param_idx += 1

        if author is not None:
            updates.append(f"author = ${param_idx}")
            params.append(author)
            param_idx += 1

        if metadata is not None:
            updates.append(f"metadata = ${param_idx}")
            params.append(metadata)
            param_idx += 1

        if not updates:
            return False

        query = f"""
            UPDATE sources
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
        """
        params.append(source_id)

        result = await self.db.execute(query, *params)
        return result == "UPDATE 1"

    async def delete(self, source_id: UUID) -> bool:
        """Delete source (cascades to contents)"""
        query = "DELETE FROM sources WHERE id = $1"
        result = await self.db.execute(query, source_id)
        return result == "DELETE 1"

    async def count_by_platform(self) -> List[Dict[str, Any]]:
        """Get source counts by platform"""
        query = """
            SELECT platform, COUNT(*) as count
            FROM sources
            GROUP BY platform
            ORDER BY count DESC
        """
        rows = await self.db.fetch(query)
        return [dict(row) for row in rows]


class ContentCRUD:
    """CRUD operations for contents table"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create(
        self,
        source_id: UUID,
        content_type: str,
        text_content: str,
        embedding: Optional[List[float]] = None,
        word_count: Optional[int] = None,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Create new content

        Args:
            source_id: Reference to source
            content_type: Content type (text, transcript, post, comment)
            text_content: The actual text content
            embedding: Vector embedding (1536 dimensions for ada-002)
            word_count: Word count (auto-calculated if None)
            language: Content language
            metadata: Content-specific metadata

        Returns:
            Content UUID
        """
        # Auto-calculate word count if not provided
        if word_count is None:
            word_count = len(text_content.split())

        # Convert embedding list to pgvector format if provided
        embedding_str = None
        if embedding:
            embedding_str = f"[{','.join(map(str, embedding))}]"

        query = """
            INSERT INTO contents (source_id, content_type, text_content, embedding, word_count, language, metadata)
            VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
            RETURNING id
        """

        content_id = await self.db.fetchval(
            query,
            source_id,
            content_type,
            text_content,
            embedding_str,
            word_count,
            language,
            metadata or {}
        )

        logger.info(f"Created content: {content_id} (type={content_type}, words={word_count}, has_embedding={embedding is not None})")
        return content_id

    async def get_by_id(self, content_id: UUID) -> Optional[Dict[str, Any]]:
        """Get content by ID"""
        query = "SELECT * FROM contents WHERE id = $1"
        row = await self.db.fetchrow(query, content_id)
        return dict(row) if row else None

    async def list_by_source(
        self,
        source_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List contents by source"""
        query = """
            SELECT * FROM contents
            WHERE source_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        rows = await self.db.fetch(query, source_id, limit, offset)
        return [dict(row) for row in rows]

    async def update_embedding(
        self,
        content_id: UUID,
        embedding: List[float]
    ) -> bool:
        """
        Update content embedding

        Args:
            content_id: Content UUID
            embedding: Vector embedding (1536 dimensions)

        Returns:
            True if updated
        """
        embedding_str = f"[{','.join(map(str, embedding))}]"

        query = """
            UPDATE contents
            SET embedding = $1::vector
            WHERE id = $2
        """

        result = await self.db.execute(query, embedding_str, content_id)
        success = result == "UPDATE 1"

        if success:
            logger.info(f"Updated embedding for content: {content_id}")

        return success

    async def delete(self, content_id: UUID) -> bool:
        """Delete content"""
        query = "DELETE FROM contents WHERE id = $1"
        result = await self.db.execute(query, content_id)
        return result == "DELETE 1"

    async def count_with_embeddings(self) -> int:
        """Count contents that have embeddings"""
        query = "SELECT COUNT(*) FROM contents WHERE embedding IS NOT NULL"
        return await self.db.fetchval(query)

    async def count_without_embeddings(self) -> int:
        """Count contents missing embeddings"""
        query = "SELECT COUNT(*) FROM contents WHERE embedding IS NULL"
        return await self.db.fetchval(query)


class ScrapeJobCRUD:
    """CRUD operations for scrape_jobs table"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create(
        self,
        url: str,
        platform: Optional[str] = None,
        depth: int = 1,
        extract_embeddings: bool = True,
    ) -> UUID:
        """
        Create new scrape job

        Args:
            url: URL to scrape
            platform: Platform hint
            depth: Scraping depth
            extract_embeddings: Whether to generate embeddings

        Returns:
            Job UUID
        """
        query = """
            INSERT INTO scrape_jobs (url, platform, depth, extract_embeddings, status)
            VALUES ($1, $2, $3, $4, 'pending')
            RETURNING id
        """

        job_id = await self.db.fetchval(query, url, platform, depth, extract_embeddings)
        logger.info(f"Created scrape job: {job_id} ({url})")
        return job_id

    async def get_by_id(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        query = "SELECT * FROM scrape_jobs WHERE id = $1"
        row = await self.db.fetchrow(query, job_id)
        return dict(row) if row else None

    async def update_status(
        self,
        job_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        items_scraped: Optional[int] = None,
    ) -> bool:
        """
        Update job status

        Args:
            job_id: Job UUID
            status: New status (pending, processing, completed, failed)
            error_message: Error message if failed
            items_scraped: Number of items scraped

        Returns:
            True if updated
        """
        updates = ["status = $1"]
        params = [status]
        param_idx = 2

        # Update timestamps based on status
        if status == "processing":
            updates.append("started_at = CURRENT_TIMESTAMP")
        elif status in ("completed", "failed"):
            updates.append("completed_at = CURRENT_TIMESTAMP")
            updates.append("processing_time_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))")

        if error_message is not None:
            updates.append(f"error_message = ${param_idx}")
            params.append(error_message)
            param_idx += 1

        if items_scraped is not None:
            updates.append(f"items_scraped = ${param_idx}")
            params.append(items_scraped)
            param_idx += 1

        params.append(job_id)

        query = f"""
            UPDATE scrape_jobs
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
        """

        result = await self.db.execute(query, *params)
        return result == "UPDATE 1"

    async def list_by_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs by status"""
        query = """
            SELECT * FROM scrape_jobs
            WHERE status = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        rows = await self.db.fetch(query, status, limit, offset)
        return [dict(row) for row in rows]

    async def list_pending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending jobs for processing"""
        return await self.list_by_status("pending", limit=limit)

    async def delete(self, job_id: UUID) -> bool:
        """Delete job"""
        query = "DELETE FROM scrape_jobs WHERE id = $1"
        result = await self.db.execute(query, job_id)
        return result == "DELETE 1"

    async def get_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        query = """
            SELECT
                status,
                COUNT(*) as count,
                AVG(processing_time_seconds) as avg_processing_time,
                SUM(items_scraped) as total_items_scraped
            FROM scrape_jobs
            GROUP BY status
        """
        rows = await self.db.fetch(query)
        return {row['status']: dict(row) for row in rows}
