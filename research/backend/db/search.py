"""
Vector similarity search using pgvector

Provides semantic search capabilities for content enrichment.
Uses cosine similarity with OpenAI ada-002 embeddings (1536 dimensions).
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from .connection import DatabaseManager

logger = logging.getLogger(__name__)


class VectorSearch:
    """Vector similarity search operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def find_similar(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.7,
        match_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to query embedding (all platforms)

        Uses cosine similarity with pgvector's <=> operator.
        Returns content with similarity score > match_threshold.

        Args:
            query_embedding: Query vector (1536 dimensions for ada-002)
            match_threshold: Minimum similarity score (0.0 to 1.0)
            match_count: Maximum number of results

        Returns:
            List of similar content with metadata and similarity scores
        """
        # Convert embedding list to pgvector format
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        query = """
            SELECT * FROM find_similar_content($1::vector, $2, $3)
        """

        rows = await self.db.fetch(query, embedding_str, match_threshold, match_count)

        results = [dict(row) for row in rows]

        logger.info(
            f"Vector search: found {len(results)} matches "
            f"(threshold={match_threshold}, limit={match_count})"
        )

        return results

    async def find_similar_by_platform(
        self,
        query_embedding: List[float],
        platform: str,
        match_threshold: float = 0.7,
        match_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find similar content from specific platform

        Args:
            query_embedding: Query vector (1536 dimensions)
            platform: Platform filter (twitter, youtube, reddit, web)
            match_threshold: Minimum similarity score
            match_count: Maximum number of results

        Returns:
            List of similar content from specified platform
        """
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        query = """
            SELECT * FROM find_similar_content_by_platform($1::vector, $2, $3, $4)
        """

        rows = await self.db.fetch(
            query,
            embedding_str,
            platform,
            match_threshold,
            match_count
        )

        results = [dict(row) for row in rows]

        logger.info(
            f"Vector search ({platform}): found {len(results)} matches "
            f"(threshold={match_threshold}, limit={match_count})"
        )

        return results

    async def find_similar_by_content_id(
        self,
        content_id: UUID,
        match_threshold: float = 0.7,
        match_count: int = 10,
        exclude_self: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to a specific content item

        Useful for "more like this" functionality.

        Args:
            content_id: Content UUID to find similar items for
            match_threshold: Minimum similarity score
            match_count: Maximum number of results
            exclude_self: Whether to exclude the source content from results

        Returns:
            List of similar content
        """
        # First, get the embedding for the specified content
        embedding_query = """
            SELECT embedding FROM contents WHERE id = $1 AND embedding IS NOT NULL
        """

        embedding_row = await self.db.fetchrow(embedding_query, content_id)

        if not embedding_row or not embedding_row['embedding']:
            logger.warning(f"Content {content_id} has no embedding")
            return []

        # Extract embedding as list
        embedding = embedding_row['embedding']

        # Now search for similar content
        embedding_str = f"[{','.join(map(str, embedding))}]"

        if exclude_self:
            # Exclude the source content
            query = """
                SELECT
                    c.id AS content_id,
                    c.source_id,
                    c.text_content,
                    1 - (c.embedding <=> $1::vector) AS similarity_score,
                    s.platform,
                    s.url,
                    s.title,
                    s.author,
                    s.published_at
                FROM contents c
                JOIN sources s ON c.source_id = s.id
                WHERE c.embedding IS NOT NULL
                    AND c.id != $2
                    AND 1 - (c.embedding <=> $1::vector) > $3
                ORDER BY c.embedding <=> $1::vector
                LIMIT $4
            """
            rows = await self.db.fetch(
                query,
                embedding_str,
                content_id,
                match_threshold,
                match_count
            )
        else:
            query = """
                SELECT * FROM find_similar_content($1::vector, $2, $3)
            """
            rows = await self.db.fetch(query, embedding_str, match_threshold, match_count)

        results = [dict(row) for row in rows]

        logger.info(
            f"Similar to {content_id}: found {len(results)} matches "
            f"(threshold={match_threshold})"
        )

        return results

    async def get_content_statistics(self) -> List[Dict[str, Any]]:
        """
        Get content statistics by platform

        Returns statistics from the database function including:
        - Platform name
        - Content count
        - Average word count
        - Total sources
        - Latest scrape timestamp
        """
        query = "SELECT * FROM get_content_statistics()"
        rows = await self.db.fetch(query)

        results = [dict(row) for row in rows]

        logger.info(f"Retrieved statistics for {len(results)} platforms")

        return results

    async def search_by_text_and_vector(
        self,
        text_query: str,
        query_embedding: List[float],
        match_threshold: float = 0.7,
        match_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: combine text search with vector similarity

        Uses PostgreSQL full-text search + pgvector similarity.
        Results are ranked by a combination of text relevance and vector similarity.

        Args:
            text_query: Text search query
            query_embedding: Query vector
            match_threshold: Minimum similarity score
            match_count: Maximum results

        Returns:
            List of matching content ranked by hybrid score
        """
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        query = """
            SELECT
                c.id AS content_id,
                c.source_id,
                c.text_content,
                1 - (c.embedding <=> $1::vector) AS similarity_score,
                ts_rank(to_tsvector('english', c.text_content), plainto_tsquery('english', $2)) AS text_rank,
                (1 - (c.embedding <=> $1::vector)) * 0.7 +
                    ts_rank(to_tsvector('english', c.text_content), plainto_tsquery('english', $2)) * 0.3 AS hybrid_score,
                s.platform,
                s.url,
                s.title,
                s.author,
                s.published_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE c.embedding IS NOT NULL
                AND (
                    to_tsvector('english', c.text_content) @@ plainto_tsquery('english', $2)
                    OR 1 - (c.embedding <=> $1::vector) > $3
                )
            ORDER BY hybrid_score DESC
            LIMIT $4
        """

        rows = await self.db.fetch(
            query,
            embedding_str,
            text_query,
            match_threshold,
            match_count
        )

        results = [dict(row) for row in rows]

        logger.info(
            f"Hybrid search for '{text_query}': found {len(results)} matches"
        )

        return results

    async def batch_find_similar(
        self,
        query_embeddings: List[List[float]],
        match_threshold: float = 0.7,
        match_count: int = 10,
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch vector search for multiple queries

        Efficiently searches for similar content for multiple embeddings.

        Args:
            query_embeddings: List of query vectors
            match_threshold: Minimum similarity score
            match_count: Maximum results per query

        Returns:
            List of result lists (one per query embedding)
        """
        results = []

        for idx, embedding in enumerate(query_embeddings):
            matches = await self.find_similar(
                embedding,
                match_threshold=match_threshold,
                match_count=match_count
            )
            results.append(matches)

        logger.info(f"Batch search: processed {len(query_embeddings)} queries")

        return results
