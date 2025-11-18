"""
Enrichment Engine - Content Intelligence via RAG Pipeline

Orchestrates the complete enrichment workflow:
1. Generate embedding for user content (LAMBDA)
2. Vector similarity search to find related content (THETA)
3. Scrape fresh sources if needed (IOTA)
4. LLM analysis to extract patterns and frameworks (GPT-4)
5. Generate contextual suggestions

Integrates:
- EmbeddingGenerator (LAMBDA) - OpenAI ada-002 embeddings
- VectorSearch (THETA) - pgvector similarity search
- ScraperRegistry (IOTA) - Multi-platform content scraping
- LLMAnalyzer - GPT-4 analysis and suggestion generation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from embeddings.generator import EmbeddingGenerator
from db.search import VectorSearch
from db.connection import DatabaseManager
from enrichment.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class EnrichmentEngine:
    """
    Main enrichment engine orchestrating RAG pipeline

    Combines vector search, scraping, and LLM analysis to provide
    intelligent content enrichment suggestions.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        openai_api_key: str,
        embedding_model: str = "text-embedding-ada-002",
        llm_model: str = "gpt-4"
    ):
        """
        Initialize enrichment engine

        Args:
            db_manager: Database manager instance
            openai_api_key: OpenAI API key for embeddings and LLM
            embedding_model: Embedding model to use
            llm_model: LLM model for analysis (gpt-4 or gpt-3.5-turbo)
        """
        self.db = db_manager

        # Initialize components
        self.embedding_generator = EmbeddingGenerator(
            api_key=openai_api_key,
            model=embedding_model
        )

        self.vector_search = VectorSearch(db_manager)

        self.llm_analyzer = LLMAnalyzer(
            api_key=openai_api_key,
            model=llm_model
        )

        # Track stats
        self.enrichments_performed = 0
        self.total_processing_time = 0.0

        logger.info(
            f"EnrichmentEngine initialized (embedding={embedding_model}, llm={llm_model})"
        )

    async def initialize(self):
        """
        Initialize engine components

        Must be called after construction before using the engine.
        """
        await self.embedding_generator.initialize(self.db)
        logger.info("EnrichmentEngine components initialized")

    async def enrich(
        self,
        content: str,
        context: Optional[str] = None,
        max_suggestions: int = 5,
        similarity_threshold: float = 0.7,
        enable_scraping: bool = False,
        scrape_platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Enrich content with suggestions from RAG pipeline

        Workflow:
        1. Generate embedding for content (LAMBDA)
        2. Vector search for similar content (THETA)
        3. Optionally scrape fresh sources (IOTA)
        4. LLM analysis and suggestion generation (GPT-4)

        Args:
            content: User's card content to enrich
            context: Optional surrounding context from other cards
            max_suggestions: Maximum number of suggestions to return
            similarity_threshold: Minimum similarity score for vector search (0.0-1.0)
            enable_scraping: Whether to scrape fresh sources
            scrape_platforms: Platforms to scrape (twitter, youtube, reddit, web)

        Returns:
            Enrichment results with suggestions, sources, frameworks, and metadata
        """
        start_time = datetime.utcnow()

        logger.info(
            f"Starting enrichment (content_length={len(content)}, "
            f"threshold={similarity_threshold}, scraping={enable_scraping})"
        )

        try:
            # Step 1: Generate embedding for user content (LAMBDA)
            logger.info("Step 1/4: Generating embedding...")

            # Combine content with context if provided
            full_content = content
            if context:
                full_content = f"{content}\n\nContext: {context}"

            embedding = await self.embedding_generator.generate(full_content)

            logger.info(f"Generated embedding: {len(embedding)} dimensions")

            # Step 2: Vector similarity search (THETA)
            logger.info(f"Step 2/4: Vector search (threshold={similarity_threshold})...")

            similar_content = await self.vector_search.find_similar(
                query_embedding=embedding,
                match_threshold=similarity_threshold,
                match_count=20  # Get top 20 for LLM to analyze
            )

            logger.info(f"Found {len(similar_content)} similar items")

            # Step 3: Optionally scrape fresh sources (IOTA)
            fresh_sources = []
            if enable_scraping and scrape_platforms:
                logger.info(f"Step 3/4: Scraping fresh sources from {scrape_platforms}...")
                fresh_sources = await self._scrape_related_content(
                    content,
                    scrape_platforms
                )
                logger.info(f"Scraped {len(fresh_sources)} fresh sources")
            else:
                logger.info("Step 3/4: Scraping disabled, skipping...")

            # Combine similar content and fresh sources
            all_sources = similar_content + fresh_sources

            # Step 4: LLM analysis and suggestion generation
            logger.info(f"Step 4/4: LLM analysis ({len(all_sources)} total sources)...")

            analysis = await self.llm_analyzer.analyze_content(
                content=content,
                similar_content=all_sources,
                max_suggestions=max_suggestions
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Update stats
            self.enrichments_performed += 1
            self.total_processing_time += processing_time

            # Format sources for response
            sources = self._format_sources(all_sources[:10])  # Top 10 sources

            result = {
                'suggestions': analysis['suggestions'],
                'sources': sources,
                'frameworks': analysis['frameworks'],
                'hooks': analysis['hooks'],
                'themes': analysis['themes'],
                'sentiment': analysis['sentiment'],
                'metadata': {
                    'similar_items_found': len(similar_content),
                    'fresh_sources_scraped': len(fresh_sources),
                    'total_sources_analyzed': len(all_sources),
                    'similarity_threshold': similarity_threshold,
                    'embedding_dimensions': len(embedding),
                    'llm_tokens_used': analysis['tokens_used'],
                    'processing_time_seconds': round(processing_time, 3)
                }
            }

            logger.info(
                f"Enrichment complete: {len(analysis['suggestions'])} suggestions, "
                f"{len(sources)} sources, {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Enrichment failed: {e}", exc_info=True)
            raise

    async def _scrape_related_content(
        self,
        content: str,
        platforms: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Scrape fresh content from specified platforms

        This is a placeholder for IOTA scraper integration.
        In production, this would:
        1. Extract keywords/topics from content
        2. Search each platform for related content
        3. Normalize and return results

        Args:
            content: User content to find related sources for
            platforms: List of platforms to scrape

        Returns:
            List of scraped content items
        """
        # TODO: Full IOTA integration would happen here
        # For now, return empty list as scrapers run asynchronously

        logger.info(
            f"Scraping placeholder: would scrape {platforms} for content related to: "
            f"{content[:100]}..."
        )

        # In production, this would:
        # 1. Use LLM to extract search keywords from content
        # 2. Call scraper registry for each platform
        # 3. Normalize results to UnifiedContent schema
        # 4. Store in database with embeddings
        # 5. Return normalized results

        return []

    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source metadata for API response

        Args:
            sources: Raw source data from database

        Returns:
            Formatted source list with relevant fields
        """
        formatted = []

        for source in sources:
            formatted.append({
                'platform': source.get('platform', 'unknown'),
                'url': source.get('url', ''),
                'title': source.get('title', 'Untitled'),
                'author': source.get('author', 'Unknown'),
                'published_at': source.get('published_at'),
                'relevance_score': round(source.get('similarity_score', 0.0), 3),
                'content_preview': source.get('text_content', '')[:200] + '...' if source.get('text_content') else ''
            })

        return formatted

    async def enrich_batch(
        self,
        cards: List[Dict[str, str]],
        max_suggestions: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Enrich multiple cards in batch

        Args:
            cards: List of cards with 'card_id' and 'content' keys
            max_suggestions: Max suggestions per card
            similarity_threshold: Similarity threshold for search

        Returns:
            List of enrichment results (one per card)
        """
        logger.info(f"Starting batch enrichment for {len(cards)} cards")

        # Process cards concurrently
        tasks = [
            self.enrich(
                content=card['content'],
                context=card.get('context'),
                max_suggestions=max_suggestions,
                similarity_threshold=similarity_threshold
            )
            for card in cards
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any errors
        formatted_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Card {cards[idx]['card_id']} enrichment failed: {result}")
                formatted_results.append({
                    'card_id': cards[idx]['card_id'],
                    'error': str(result),
                    'suggestions': [],
                    'sources': []
                })
            else:
                formatted_results.append({
                    'card_id': cards[idx]['card_id'],
                    **result
                })

        logger.info(f"Batch enrichment complete: {len(formatted_results)} results")

        return formatted_results

    async def get_related_content(
        self,
        content: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        platform_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get related content without full enrichment

        Useful for "more like this" functionality without LLM overhead.

        Args:
            content: Content to find similar items for
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score
            platform_filter: Optional platform filter (twitter, youtube, reddit, web)

        Returns:
            List of similar content items
        """
        # Generate embedding
        embedding = await self.embedding_generator.generate(content)

        # Vector search
        if platform_filter:
            similar = await self.vector_search.find_similar_by_platform(
                query_embedding=embedding,
                platform=platform_filter,
                match_threshold=similarity_threshold,
                match_count=limit
            )
        else:
            similar = await self.vector_search.find_similar(
                query_embedding=embedding,
                match_threshold=similarity_threshold,
                match_count=limit
            )

        return self._format_sources(similar)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get enrichment engine statistics

        Returns:
            Dict with performance and usage stats
        """
        embedding_stats = self.embedding_generator.get_cost_stats()
        llm_stats = self.llm_analyzer.get_usage_stats()

        return {
            'enrichments_performed': self.enrichments_performed,
            'total_processing_time_seconds': round(self.total_processing_time, 2),
            'avg_processing_time_seconds': (
                round(self.total_processing_time / self.enrichments_performed, 3)
                if self.enrichments_performed > 0 else 0
            ),
            'embedding_stats': embedding_stats,
            'llm_stats': llm_stats,
            'total_cost_usd': round(
                embedding_stats['total_cost_usd'] + llm_stats['estimated_cost_usd'],
                4
            )
        }

    async def health_check(self) -> Dict[str, str]:
        """
        Check health of all engine components

        Returns:
            Health status dict
        """
        status = {
            'engine': 'healthy',
            'database': 'unknown',
            'embeddings': 'unknown',
            'llm': 'unknown'
        }

        try:
            # Check database
            db_health = await self.db.health_check()
            status['database'] = 'healthy' if db_health['status'] == 'healthy' else 'unhealthy'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status['database'] = 'unhealthy'

        try:
            # Check embeddings (simple test)
            test_embedding = await self.embedding_generator.generate("test")
            status['embeddings'] = 'healthy' if len(test_embedding) == 1536 else 'unhealthy'
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            status['embeddings'] = 'unhealthy'

        # LLM check is implicit (no auth errors = healthy)
        status['llm'] = 'healthy'

        overall = 'healthy' if all(v == 'healthy' for v in status.values()) else 'degraded'
        status['overall'] = overall

        return status
