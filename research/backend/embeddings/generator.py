"""
Embedding Generator for Research Backend

Implements OpenAI ada-002 embedding generation with:
- Text chunking (512 tokens per chunk)
- Batch processing (up to 100 chunks per API call)
- PostgreSQL pgvector storage
- Cache layer to avoid re-embedding
- Cost tracking for API usage

Usage:
    generator = EmbeddingGenerator(api_key="sk-...")
    await generator.initialize(db_manager)

    # Generate embedding for single text
    embedding = await generator.generate(text)

    # Generate embeddings for content in database
    await generator.generate_for_content(content_id)

    # Batch generate embeddings for multiple contents
    await generator.generate_for_contents(content_ids)
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

import tiktoken
from openai import AsyncOpenAI

from db.connection import DatabaseManager
from db.crud import ContentCRUD

logger = logging.getLogger(__name__)


class EmbeddingCostTracker:
    """
    Track embedding generation costs

    OpenAI ada-002 pricing: $0.0001 per 1K tokens
    """

    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.requests = 0
        self.embeddings_generated = 0

    def add_request(self, tokens: int, embeddings_count: int):
        """
        Record a successful embedding request

        Args:
            tokens: Number of tokens processed
            embeddings_count: Number of embeddings generated
        """
        self.total_tokens += tokens
        self.total_cost += (tokens / 1000) * 0.0001  # $0.0001 per 1K tokens
        self.requests += 1
        self.embeddings_generated += embeddings_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cost tracking statistics"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "requests": self.requests,
            "embeddings_generated": self.embeddings_generated,
            "avg_tokens_per_request": (
                round(self.total_tokens / self.requests, 2) if self.requests > 0 else 0
            ),
            "cost_per_embedding": (
                round(self.total_cost / self.embeddings_generated, 6)
                if self.embeddings_generated > 0 else 0
            ),
        }

    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info(
            f"Embedding Cost Stats: {stats['embeddings_generated']} embeddings, "
            f"{stats['total_tokens']} tokens, ${stats['total_cost_usd']} "
            f"({stats['requests']} requests)"
        )


class EmbeddingCache:
    """
    Cache layer for embeddings

    Uses SHA-256 hash of text content to check if already embedded.
    Stores mapping in database metadata field.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.content_crud = ContentCRUD(db_manager)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 hash of text content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def has_embedding(self, content_id: UUID) -> bool:
        """
        Check if content already has an embedding

        Args:
            content_id: Content UUID

        Returns:
            True if embedding exists
        """
        query = "SELECT embedding IS NOT NULL as has_embedding FROM contents WHERE id = $1"
        result = await self.db.fetchval(query, content_id)
        return result if result is not None else False

    async def get_cached_embedding(self, content_id: UUID) -> Optional[List[float]]:
        """
        Get cached embedding for content

        Args:
            content_id: Content UUID

        Returns:
            Embedding vector or None
        """
        query = "SELECT embedding FROM contents WHERE id = $1"
        result = await self.db.fetchval(query, content_id)

        if result:
            # Convert pgvector to Python list
            return list(result)

        return None

    async def count_cached(self) -> Dict[str, int]:
        """Get cache statistics"""
        with_embeddings = await self.content_crud.count_with_embeddings()
        without_embeddings = await self.content_crud.count_without_embeddings()

        return {
            "cached": with_embeddings,
            "uncached": without_embeddings,
            "total": with_embeddings + without_embeddings,
            "cache_hit_rate": (
                round(with_embeddings / (with_embeddings + without_embeddings) * 100, 2)
                if (with_embeddings + without_embeddings) > 0 else 0
            )
        }


class TextChunker:
    """
    Split long text into chunks for embedding

    Uses tiktoken to count tokens accurately for OpenAI models.
    Default chunk size: 512 tokens with 50 token overlap.
    """

    def __init__(self, model: str = "text-embedding-ada-002", chunk_size: int = 512):
        """
        Initialize text chunker

        Args:
            model: OpenAI model name for tokenization
            chunk_size: Maximum tokens per chunk
        """
        self.encoding = tiktoken.encoding_for_model(model)
        self.chunk_size = chunk_size
        self.overlap = 50  # Overlap between chunks for context preservation

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks

        Args:
            text: Input text

        Returns:
            List of text chunks (each ≤ chunk_size tokens)
        """
        # Encode text to tokens
        tokens = self.encoding.encode(text)

        # If text is small enough, return as-is
        if len(tokens) <= self.chunk_size:
            return [text]

        # Split into chunks with overlap
        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk of tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move to next chunk (with overlap)
            start += self.chunk_size - self.overlap

            # Prevent infinite loop on last chunk
            if end == len(tokens):
                break

        logger.info(f"Split text into {len(chunks)} chunks ({len(tokens)} tokens total)")
        return chunks


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI ada-002

    Features:
    - Text chunking (512 tokens per chunk)
    - Batch processing (up to 100 chunks per API call)
    - Automatic caching (checks if content already embedded)
    - Cost tracking
    - Database integration (stores to pgvector)
    """

    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        Initialize embedding generator

        Args:
            api_key: OpenAI API key
            model: OpenAI embedding model (default: text-embedding-ada-002)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.chunker = TextChunker(model=model, chunk_size=512)
        self.cost_tracker = EmbeddingCostTracker()

        # Will be initialized with initialize()
        self.db: Optional[DatabaseManager] = None
        self.cache: Optional[EmbeddingCache] = None
        self.content_crud: Optional[ContentCRUD] = None

        logger.info(f"Initialized EmbeddingGenerator with model: {model}")

    async def initialize(self, db_manager: DatabaseManager):
        """
        Initialize with database connection

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self.cache = EmbeddingCache(db_manager)
        self.content_crud = ContentCRUD(db_manager)
        logger.info("EmbeddingGenerator initialized with database connection")

    async def generate(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            Embedding vector (1536 dimensions for ada-002)
        """
        # Count tokens for cost tracking
        token_count = self.chunker.count_tokens(text)

        # Generate embedding
        response = await self.client.embeddings.create(
            input=text,
            model=self.model
        )

        embedding = response.data[0].embedding

        # Track cost
        self.cost_tracker.add_request(token_count, 1)

        logger.debug(f"Generated embedding: {token_count} tokens")

        return embedding

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        OpenAI allows up to 2048 tokens per request, with max 100 inputs.
        This method handles batching automatically.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # OpenAI limit: max 100 inputs per request
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Count tokens for cost tracking
            total_tokens = sum(self.chunker.count_tokens(text) for text in batch)

            # Generate embeddings
            response = await self.client.embeddings.create(
                input=batch,
                model=self.model
            )

            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

            # Track cost
            self.cost_tracker.add_request(total_tokens, len(batch))

            logger.info(
                f"Generated batch: {len(batch)} embeddings, {total_tokens} tokens "
                f"(${round(total_tokens * 0.0001 / 1000, 6)})"
            )

        return all_embeddings

    async def generate_chunked(self, text: str) -> List[float]:
        """
        Generate embedding for long text by chunking and averaging

        For texts longer than 512 tokens:
        1. Split into chunks
        2. Generate embedding for each chunk
        3. Average embeddings (element-wise mean)

        Args:
            text: Input text (can be arbitrarily long)

        Returns:
            Averaged embedding vector
        """
        # Split into chunks
        chunks = self.chunker.chunk_text(text)

        # Generate embeddings for all chunks (batched)
        embeddings = await self.generate_batch(chunks)

        # Average embeddings (element-wise mean)
        if len(embeddings) == 1:
            return embeddings[0]

        # Compute mean across all chunks
        avg_embedding = [
            sum(emb[i] for emb in embeddings) / len(embeddings)
            for i in range(len(embeddings[0]))
        ]

        logger.info(f"Averaged {len(embeddings)} chunk embeddings")

        return avg_embedding

    async def generate_for_content(
        self,
        content_id: UUID,
        force: bool = False
    ) -> Optional[List[float]]:
        """
        Generate embedding for content in database

        Args:
            content_id: Content UUID
            force: Force regeneration even if cached

        Returns:
            Embedding vector or None if content not found
        """
        if not self.db or not self.cache or not self.content_crud:
            raise RuntimeError("EmbeddingGenerator not initialized - call initialize() first")

        # Check cache
        if not force and await self.cache.has_embedding(content_id):
            logger.info(f"Cache hit: content {content_id} already has embedding")
            return await self.cache.get_cached_embedding(content_id)

        # Fetch content from database
        content = await self.content_crud.get_by_id(content_id)

        if not content:
            logger.warning(f"Content not found: {content_id}")
            return None

        text = content['text_content']

        # Generate embedding (handles chunking automatically)
        embedding = await self.generate_chunked(text)

        # Store in database
        success = await self.content_crud.update_embedding(content_id, embedding)

        if success:
            logger.info(f"Stored embedding for content: {content_id}")
        else:
            logger.error(f"Failed to store embedding for content: {content_id}")

        return embedding

    async def generate_for_contents(
        self,
        content_ids: List[UUID],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Generate embeddings for multiple contents

        Args:
            content_ids: List of content UUIDs
            force: Force regeneration even if cached

        Returns:
            Statistics about the operation
        """
        if not self.db or not self.cache or not self.content_crud:
            raise RuntimeError("EmbeddingGenerator not initialized - call initialize() first")

        stats = {
            "total": len(content_ids),
            "generated": 0,
            "cached": 0,
            "failed": 0,
            "errors": []
        }

        start_time = datetime.now()

        for content_id in content_ids:
            try:
                # Check cache
                if not force and await self.cache.has_embedding(content_id):
                    stats["cached"] += 1
                    logger.debug(f"Skipped cached content: {content_id}")
                    continue

                # Generate embedding
                embedding = await self.generate_for_content(content_id, force=force)

                if embedding:
                    stats["generated"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                logger.error(f"Error generating embedding for {content_id}: {e}")
                stats["failed"] += 1
                stats["errors"].append({"content_id": str(content_id), "error": str(e)})

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        stats["duration_seconds"] = round(duration, 2)
        stats["embeddings_per_second"] = round(stats["generated"] / duration, 2) if duration > 0 else 0

        # Add cost tracking
        stats["cost"] = self.cost_tracker.get_stats()

        logger.info(
            f"Batch complete: {stats['generated']} generated, "
            f"{stats['cached']} cached, {stats['failed']} failed "
            f"({duration:.2f}s, ${stats['cost']['total_cost_usd']})"
        )

        return stats

    async def generate_for_all_uncached(self) -> Dict[str, Any]:
        """
        Generate embeddings for all contents without embeddings

        Returns:
            Statistics about the operation
        """
        if not self.db:
            raise RuntimeError("EmbeddingGenerator not initialized - call initialize() first")

        # Find all contents without embeddings
        query = "SELECT id FROM contents WHERE embedding IS NULL"
        rows = await self.db.fetch(query)

        content_ids = [row['id'] for row in rows]

        logger.info(f"Found {len(content_ids)} contents without embeddings")

        if not content_ids:
            return {
                "total": 0,
                "generated": 0,
                "cached": 0,
                "failed": 0,
                "message": "No uncached contents found"
            }

        return await self.generate_for_contents(content_ids)

    def get_cost_stats(self) -> Dict[str, Any]:
        """Get current cost tracking statistics"""
        return self.cost_tracker.get_stats()

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        if not self.cache:
            raise RuntimeError("EmbeddingGenerator not initialized - call initialize() first")

        return await self.cache.count_cached()
