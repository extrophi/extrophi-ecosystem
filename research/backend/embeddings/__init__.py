"""
Embedding generation module for Research Backend

Provides OpenAI ada-002 embedding generation with:
- Text chunking (512 tokens)
- Batch processing (100 chunks per request)
- PostgreSQL vector storage
- Cache layer (avoid re-embedding)
- Cost tracking
"""

from .generator import EmbeddingGenerator, EmbeddingCache, EmbeddingCostTracker

__all__ = ["EmbeddingGenerator", "EmbeddingCache", "EmbeddingCostTracker"]
