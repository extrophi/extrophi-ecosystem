"""
Unified Timeline for Multi-Source Aggregation

Combines content from multiple platforms (Twitter, YouTube, Reddit, Web) into a single
chronological timeline with deduplication and filtering capabilities.

Agent: CHI-2
Purpose: Multi-source aggregation for unified content view
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID

from db.connection import DatabaseManager

logger = logging.getLogger(__name__)


class UnifiedTimeline:
    """
    Unified timeline aggregator for multi-platform content

    Features:
    - Combines content from multiple platforms
    - Source filtering (show/hide specific platforms)
    - Deduplication using vector similarity
    - Chronological sorting
    - Pagination support
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize unified timeline

        Args:
            db_manager: Database connection manager
        """
        self.db = db_manager

    async def get_timeline(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        deduplicate: bool = True,
        similarity_threshold: float = 0.85,
    ) -> Dict[str, Any]:
        """
        Get unified timeline across multiple platforms

        Args:
            platforms: List of platforms to include (None = all platforms)
            limit: Maximum number of results
            offset: Pagination offset
            sort_by: Sort field (published_at, scraped_at, relevance)
            sort_order: Sort order (asc, desc)
            deduplicate: Whether to deduplicate similar content
            similarity_threshold: Similarity threshold for deduplication (0.0-1.0)

        Returns:
            Dictionary containing:
                - items: List of unified content items
                - total: Total count (before pagination)
                - platforms: Platforms included in results
                - deduplicated_count: Number of items removed by deduplication
        """
        logger.info(
            f"Getting unified timeline: platforms={platforms}, limit={limit}, "
            f"offset={offset}, deduplicate={deduplicate}"
        )

        # Build platform filter clause
        platform_clause = ""
        params = []
        param_idx = 1

        if platforms:
            placeholders = ", ".join([f"${i}" for i in range(param_idx, param_idx + len(platforms))])
            platform_clause = f"AND s.platform IN ({placeholders})"
            params.extend(platforms)
            param_idx += len(platforms)

        # Validate sort_by field
        allowed_sort_fields = ["published_at", "scraped_at", "word_count"]
        if sort_by not in allowed_sort_fields:
            sort_by = "published_at"

        # Validate sort_order
        sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"

        # Build SQL query with NULLS LAST to handle NULL published_at
        query = f"""
            SELECT
                c.id AS content_id,
                c.source_id,
                c.content_type,
                c.text_content,
                c.word_count,
                c.language,
                c.metadata AS content_metadata,
                c.embedding,
                c.created_at AS content_created_at,
                s.id AS source_id,
                s.platform,
                s.url,
                s.title,
                s.author,
                s.published_at,
                s.metadata AS source_metadata,
                s.scraped_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE 1=1
            {platform_clause}
            ORDER BY
                CASE WHEN s.{sort_by} IS NULL THEN 1 ELSE 0 END,
                s.{sort_by} {sort_order}
        """

        # First, get total count (before pagination and deduplication)
        count_query = f"""
            SELECT COUNT(*) as total
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE 1=1
            {platform_clause}
        """

        count_result = await self.db.fetchrow(count_query, *params)
        total_count = count_result['total'] if count_result else 0

        # Fetch content with larger limit if deduplication is enabled
        # (we'll deduplicate and then paginate)
        fetch_limit = limit * 3 if deduplicate else limit
        fetch_query = query + f" LIMIT {fetch_limit} OFFSET ${param_idx}"
        params.append(offset)

        rows = await self.db.fetch(fetch_query, *params)

        # Convert to list of dicts
        items = [dict(row) for row in rows]

        # Deduplication logic
        deduplicated_count = 0
        if deduplicate and len(items) > 1:
            items, deduplicated_count = await self._deduplicate_items(
                items,
                similarity_threshold
            )

        # Apply pagination after deduplication
        paginated_items = items[0:limit]

        # Get unique platforms in results
        platforms_in_results = list(set(item['platform'] for item in paginated_items))

        # Format response
        response = {
            "items": [self._format_item(item) for item in paginated_items],
            "total": total_count,
            "count": len(paginated_items),
            "platforms": sorted(platforms_in_results),
            "deduplicated_count": deduplicated_count,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(paginated_items)) < total_count
            }
        }

        logger.info(
            f"Timeline retrieved: {len(paginated_items)} items from {len(platforms_in_results)} platforms "
            f"(deduplicated: {deduplicated_count})"
        )

        return response

    async def _deduplicate_items(
        self,
        items: List[Dict[str, Any]],
        similarity_threshold: float
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Deduplicate items based on embedding similarity

        Uses cosine similarity between embeddings to detect duplicate content.
        Keeps the earliest published item when duplicates are found.

        Args:
            items: List of content items with embeddings
            similarity_threshold: Cosine similarity threshold (0.0-1.0)

        Returns:
            Tuple of (deduplicated_items, number_of_duplicates_removed)
        """
        if not items:
            return items, 0

        # Track items to keep and items to skip
        kept_items = []
        seen_content_ids: Set[UUID] = set()
        duplicate_groups: List[List[int]] = []  # Track which items are similar

        # Only consider items with embeddings
        items_with_embeddings = [
            (idx, item) for idx, item in enumerate(items)
            if item.get('embedding') is not None
        ]

        # If no embeddings, return all items (can't deduplicate)
        if not items_with_embeddings:
            logger.info("No embeddings available for deduplication")
            return items, 0

        # Compare each item with previously kept items
        for idx, item in enumerate(items):
            content_id = item['content_id']

            # Skip if already marked as duplicate
            if content_id in seen_content_ids:
                continue

            # If no embedding, keep it (can't compare)
            if item.get('embedding') is None:
                kept_items.append(item)
                seen_content_ids.add(content_id)
                continue

            # Check similarity with already kept items
            is_duplicate = False
            for kept_item in kept_items:
                if kept_item.get('embedding') is None:
                    continue

                similarity = self._cosine_similarity(
                    item['embedding'],
                    kept_item['embedding']
                )

                if similarity >= similarity_threshold:
                    # Duplicate found - keep the one with earlier published_at
                    is_duplicate = True

                    # If current item is older, replace kept_item
                    item_published = item.get('published_at')
                    kept_published = kept_item.get('published_at')

                    # Handle None published_at (use scraped_at as fallback)
                    if item_published is None:
                        item_published = item.get('scraped_at')
                    if kept_published is None:
                        kept_published = kept_item.get('scraped_at')

                    if item_published and kept_published and item_published < kept_published:
                        # Current item is older, replace the kept one
                        kept_items.remove(kept_item)
                        seen_content_ids.discard(kept_item['content_id'])
                        kept_items.append(item)
                        seen_content_ids.add(content_id)

                    break

            if not is_duplicate:
                kept_items.append(item)
                seen_content_ids.add(content_id)

        duplicates_removed = len(items) - len(kept_items)

        if duplicates_removed > 0:
            logger.info(
                f"Deduplication: removed {duplicates_removed} duplicates "
                f"(threshold={similarity_threshold})"
            )

        return kept_items, duplicates_removed

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _format_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format timeline item for API response

        Args:
            item: Raw database item

        Returns:
            Formatted item with standardized structure
        """
        # Remove embedding from response (too large)
        formatted = {
            "content_id": str(item['content_id']),
            "platform": item['platform'],
            "content_type": item['content_type'],
            "title": item.get('title'),
            "text_content": item['text_content'],
            "word_count": item.get('word_count'),
            "language": item.get('language', 'en'),
            "author": item.get('author'),
            "url": item['url'],
            "published_at": item.get('published_at').isoformat() if item.get('published_at') else None,
            "scraped_at": item.get('scraped_at').isoformat() if item.get('scraped_at') else None,
            "metadata": {
                **item.get('source_metadata', {}),
                **item.get('content_metadata', {})
            }
        }

        return formatted

    async def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available content by platform

        Returns:
            Dictionary with platform counts and metadata
        """
        query = """
            SELECT
                s.platform,
                COUNT(DISTINCT c.id) as content_count,
                COUNT(DISTINCT s.id) as source_count,
                COUNT(DISTINCT s.author) as author_count,
                AVG(c.word_count) as avg_word_count,
                MIN(s.published_at) as earliest_published,
                MAX(s.published_at) as latest_published,
                MAX(s.scraped_at) as latest_scraped
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            GROUP BY s.platform
            ORDER BY content_count DESC
        """

        rows = await self.db.fetch(query)

        statistics = {
            "platforms": [],
            "total_content": 0,
            "total_sources": 0,
            "total_authors": 0
        }

        for row in rows:
            platform_stats = {
                "platform": row['platform'],
                "content_count": row['content_count'],
                "source_count": row['source_count'],
                "author_count": row['author_count'],
                "avg_word_count": float(row['avg_word_count']) if row['avg_word_count'] else 0,
                "earliest_published": row['earliest_published'].isoformat() if row['earliest_published'] else None,
                "latest_published": row['latest_published'].isoformat() if row['latest_published'] else None,
                "latest_scraped": row['latest_scraped'].isoformat() if row['latest_scraped'] else None,
            }
            statistics["platforms"].append(platform_stats)
            statistics["total_content"] += row['content_count']
            statistics["total_sources"] += row['source_count']
            statistics["total_authors"] += row['author_count']

        logger.info(
            f"Platform statistics: {len(statistics['platforms'])} platforms, "
            f"{statistics['total_content']} total content items"
        )

        return statistics

    async def filter_by_author(
        self,
        author: str,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get timeline filtered by author across platforms

        Args:
            author: Author name/username to filter by
            platforms: Optional list of platforms to include
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Timeline filtered by author
        """
        logger.info(f"Getting timeline for author: {author}")

        platform_clause = ""
        params = [author]
        param_idx = 2

        if platforms:
            placeholders = ", ".join([f"${i}" for i in range(param_idx, param_idx + len(platforms))])
            platform_clause = f"AND s.platform IN ({placeholders})"
            params.extend(platforms)
            param_idx += len(platforms)

        query = f"""
            SELECT
                c.id AS content_id,
                c.source_id,
                c.content_type,
                c.text_content,
                c.word_count,
                c.language,
                c.metadata AS content_metadata,
                c.created_at AS content_created_at,
                s.platform,
                s.url,
                s.title,
                s.author,
                s.published_at,
                s.metadata AS source_metadata,
                s.scraped_at
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE s.author ILIKE $1
            {platform_clause}
            ORDER BY s.published_at DESC NULLS LAST
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        params.extend([limit, offset])

        rows = await self.db.fetch(query, *params)
        items = [self._format_item(dict(row)) for row in rows]

        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM contents c
            JOIN sources s ON c.source_id = s.id
            WHERE s.author ILIKE $1
            {platform_clause}
        """

        count_params = [author]
        if platforms:
            count_params.extend(platforms)

        count_result = await self.db.fetchrow(count_query, *count_params)
        total_count = count_result['total'] if count_result else 0

        return {
            "items": items,
            "author": author,
            "total": total_count,
            "count": len(items),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(items)) < total_count
            }
        }
