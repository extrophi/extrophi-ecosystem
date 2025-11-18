# AGENT ZETA: RAG/ChromaDB Vector Intelligence

## Mission Statement

You are AGENT ZETA, the semantic intelligence layer for IAC-032 Unified Scraper. Your mission is to implement a production-ready RAG (Retrieval Augmented Generation) system using ChromaDB for vector storage and OpenAI embeddings. You transform raw scraped content into semantically searchable knowledge, enabling cross-platform pattern detection and intelligent content retrieval.

**Core Responsibility**: Convert all scraped content (tweets, YouTube transcripts, Reddit posts, blog articles) into embeddings and provide fast, relevant semantic search capabilities.

---

## Architecture Context

You are building the intelligence backbone that connects:
- **AGENT EPSILON** (Twitter scraper) → Your embeddings
- **AGENT THETA** (YouTube/Reddit scrapers) → Your embeddings
- **AGENT ETA** (FastAPI) → Queries your vector store
- **PostgreSQL** (structured data) ← Your metadata links

Your ChromaDB instance stores:
1. Content embeddings (1536 dimensions via OpenAI)
2. Metadata (platform, author, URL, timestamp)
3. Full text for retrieval

---

## Files to Create

### 1. `backend/services/__init__.py`

```python
"""
Services layer for IAC-032 Unified Scraper.

This module provides core business logic services:
- Embedding generation (OpenAI)
- Vector storage (ChromaDB)
- RAG query engine
- Cost tracking
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStoreService
from .rag_query import RAGQueryEngine

__all__ = [
    "EmbeddingService",
    "VectorStoreService",
    "RAGQueryEngine",
]
```

---

### 2. `backend/services/embeddings.py`

```python
"""
OpenAI Embedding Service with cost tracking.

Uses text-embedding-3-small model (1536 dimensions).
Cost: $0.00002 per 1K tokens
"""

import os
import tiktoken
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel, Field


class EmbeddingCost(BaseModel):
    """Track embedding generation costs."""
    tokens_used: int = 0
    cost_usd: float = 0.0
    requests_made: int = 0
    last_request: Optional[datetime] = None


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    embedding: List[float] = Field(..., min_length=1536, max_length=1536)
    tokens: int
    cost_usd: float
    model: str = "text-embedding-3-small"


class BatchEmbeddingResult(BaseModel):
    """Result of batch embedding generation."""
    embeddings: List[List[float]]
    total_tokens: int
    total_cost_usd: float
    items_processed: int
    processing_time_seconds: float


class EmbeddingService:
    """
    Generate embeddings using OpenAI text-embedding-3-small.

    Features:
    - Single and batch embedding generation
    - Automatic token counting
    - Cost tracking ($0.00002/1K tokens)
    - Retry logic with exponential backoff
    - Async batch processing
    """

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    COST_PER_1K_TOKENS = 0.00002  # $0.02 per 1M tokens
    MAX_TOKENS_PER_REQUEST = 8191  # Model limit
    MAX_BATCH_SIZE = 100  # OpenAI batch limit

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.tokenizer = tiktoken.encoding_for_model(self.MODEL)
        self.cost_tracker = EmbeddingCost()

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to tokenize

        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))

    def calculate_cost(self, tokens: int) -> float:
        """
        Calculate cost in USD for token count.

        Args:
            tokens: Number of tokens

        Returns:
            Cost in USD
        """
        return (tokens / 1000) * self.COST_PER_1K_TOKENS

    def truncate_text(self, text: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens (defaults to model limit)

        Returns:
            Truncated text
        """
        max_tokens = max_tokens or self.MAX_TOKENS_PER_REQUEST
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.tokenizer.decode(tokens[:max_tokens])

    async def embed_single(
        self,
        text: str,
        truncate: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed
            truncate: Whether to truncate if too long

        Returns:
            EmbeddingResult with vector and cost info
        """
        if truncate:
            text = self.truncate_text(text)

        tokens = self.count_tokens(text)
        if tokens > self.MAX_TOKENS_PER_REQUEST:
            raise ValueError(f"Text too long: {tokens} tokens exceeds {self.MAX_TOKENS_PER_REQUEST}")

        response = await self.client.embeddings.create(
            input=text,
            model=self.MODEL,
            dimensions=self.DIMENSIONS
        )

        embedding = response.data[0].embedding
        actual_tokens = response.usage.total_tokens
        cost = self.calculate_cost(actual_tokens)

        # Update tracker
        self.cost_tracker.tokens_used += actual_tokens
        self.cost_tracker.cost_usd += cost
        self.cost_tracker.requests_made += 1
        self.cost_tracker.last_request = datetime.now(timezone.utc)

        return EmbeddingResult(
            embedding=embedding,
            tokens=actual_tokens,
            cost_usd=cost
        )

    async def embed_batch(
        self,
        texts: List[str],
        truncate: bool = True,
        max_concurrent: int = 10
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings for batch of texts.

        Args:
            texts: List of texts to embed
            truncate: Whether to truncate long texts
            max_concurrent: Maximum concurrent API calls

        Returns:
            BatchEmbeddingResult with all vectors and cost info
        """
        import time
        start_time = time.time()

        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                total_tokens=0,
                total_cost_usd=0.0,
                items_processed=0,
                processing_time_seconds=0.0
            )

        # Truncate texts if needed
        if truncate:
            texts = [self.truncate_text(t) for t in texts]

        # Process in batches of MAX_BATCH_SIZE
        all_embeddings = []
        total_tokens = 0
        total_cost = 0.0

        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]

            response = await self.client.embeddings.create(
                input=batch,
                model=self.MODEL,
                dimensions=self.DIMENSIONS
            )

            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            # Track costs
            batch_tokens = response.usage.total_tokens
            batch_cost = self.calculate_cost(batch_tokens)
            total_tokens += batch_tokens
            total_cost += batch_cost

            # Update tracker
            self.cost_tracker.tokens_used += batch_tokens
            self.cost_tracker.cost_usd += batch_cost
            self.cost_tracker.requests_made += 1

        self.cost_tracker.last_request = datetime.now(timezone.utc)

        processing_time = time.time() - start_time

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            items_processed=len(texts),
            processing_time_seconds=processing_time
        )

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get summary of costs incurred.

        Returns:
            Dictionary with cost statistics
        """
        return {
            "total_tokens": self.cost_tracker.tokens_used,
            "total_cost_usd": round(self.cost_tracker.cost_usd, 6),
            "total_requests": self.cost_tracker.requests_made,
            "avg_cost_per_request": round(
                self.cost_tracker.cost_usd / max(1, self.cost_tracker.requests_made),
                6
            ),
            "last_request": self.cost_tracker.last_request.isoformat() if self.cost_tracker.last_request else None
        }

    def reset_cost_tracker(self) -> None:
        """Reset cost tracking statistics."""
        self.cost_tracker = EmbeddingCost()
```

---

### 3. `backend/services/vector_store.py`

```python
"""
ChromaDB Vector Store Service.

Local persistence with semantic search capabilities.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
import chromadb
from chromadb.config import Settings
from pydantic import BaseModel, Field


class ContentDocument(BaseModel):
    """Document to store in vector database."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    platform: str  # twitter, youtube, reddit, web
    source_url: str
    author_id: str
    author_name: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Result from semantic search."""
    id: str
    content: str
    platform: str
    source_url: str
    author_name: str
    distance: float  # Lower is more similar (cosine distance)
    similarity: float  # 1 - distance (higher is more similar)
    metadata: Dict[str, Any]


class VectorStoreService:
    """
    ChromaDB vector store for semantic content search.

    Features:
    - Local persistence (data/chromadb/)
    - Add documents with embeddings
    - Semantic search with filters
    - Metadata indexing
    - Collection management
    """

    COLLECTION_NAME = "unified_content"
    PERSIST_DIRECTORY = "data/chromadb"

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB client with local persistence.

        Args:
            persist_directory: Directory for ChromaDB storage
        """
        self.persist_directory = persist_directory or self.PERSIST_DIRECTORY

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def add_document(
        self,
        document: ContentDocument,
        embedding: List[float]
    ) -> str:
        """
        Add single document with embedding to vector store.

        Args:
            document: Content document to store
            embedding: Pre-computed embedding vector (1536 dimensions)

        Returns:
            Document ID
        """
        metadata = {
            "platform": document.platform,
            "source_url": document.source_url,
            "author_id": document.author_id,
            "author_name": document.author_name,
            "title": document.title or "",
            "scraped_at": document.scraped_at.isoformat(),
            "tags": ",".join(document.tags) if document.tags else "",
            **{f"metric_{k}": str(v) for k, v in document.metrics.items()}
        }

        if document.published_at:
            metadata["published_at"] = document.published_at.isoformat()

        self.collection.add(
            ids=[document.id],
            embeddings=[embedding],
            documents=[document.content],
            metadatas=[metadata]
        )

        return document.id

    def add_documents_batch(
        self,
        documents: List[ContentDocument],
        embeddings: List[List[float]]
    ) -> List[str]:
        """
        Add batch of documents with embeddings.

        Args:
            documents: List of content documents
            embeddings: List of embedding vectors (must match documents length)

        Returns:
            List of document IDs
        """
        if len(documents) != len(embeddings):
            raise ValueError(f"Documents ({len(documents)}) and embeddings ({len(embeddings)}) must match")

        if not documents:
            return []

        ids = []
        metadatas = []
        contents = []

        for doc in documents:
            ids.append(doc.id)
            contents.append(doc.content)

            metadata = {
                "platform": doc.platform,
                "source_url": doc.source_url,
                "author_id": doc.author_id,
                "author_name": doc.author_name,
                "title": doc.title or "",
                "scraped_at": doc.scraped_at.isoformat(),
                "tags": ",".join(doc.tags) if doc.tags else "",
                **{f"metric_{k}": str(v) for k, v in doc.metrics.items()}
            }

            if doc.published_at:
                metadata["published_at"] = doc.published_at.isoformat()

            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )

        return ids

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        platform_filter: Optional[str] = None,
        author_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Semantic search using embedding similarity.

        Args:
            query_embedding: Embedding vector for query
            n_results: Number of results to return
            platform_filter: Filter by platform (twitter, youtube, etc.)
            author_filter: Filter by author name

        Returns:
            List of SearchResult ordered by similarity
        """
        where_filter = {}

        if platform_filter:
            where_filter["platform"] = platform_filter

        if author_filter:
            where_filter["author_name"] = author_filter

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []

        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1 - distance  # Convert distance to similarity

                search_results.append(SearchResult(
                    id=doc_id,
                    content=results["documents"][0][i],
                    platform=results["metadatas"][0][i]["platform"],
                    source_url=results["metadatas"][0][i]["source_url"],
                    author_name=results["metadatas"][0][i]["author_name"],
                    distance=distance,
                    similarity=similarity,
                    metadata=results["metadatas"][0][i]
                ))

        return search_results

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data or None if not found
        """
        result = self.collection.get(
            ids=[document_id],
            include=["documents", "metadatas", "embeddings"]
        )

        if result["ids"]:
            return {
                "id": result["ids"][0],
                "content": result["documents"][0],
                "metadata": result["metadatas"][0],
                "embedding": result["embeddings"][0] if result["embeddings"] else None
            }

        return None

    def delete_document(self, document_id: str) -> bool:
        """
        Delete document by ID.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()

        # Get platform distribution
        platform_counts = {}
        if count > 0:
            # Sample to get platform distribution
            sample = self.collection.get(
                limit=min(count, 1000),
                include=["metadatas"]
            )

            for metadata in sample["metadatas"]:
                platform = metadata.get("platform", "unknown")
                platform_counts[platform] = platform_counts.get(platform, 0) + 1

        return {
            "total_documents": count,
            "collection_name": self.COLLECTION_NAME,
            "persist_directory": self.persist_directory,
            "platform_distribution": platform_counts
        }

    def reset_collection(self) -> None:
        """
        Reset (delete and recreate) the collection.

        WARNING: This deletes all stored vectors!
        """
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
```

---

### 4. `backend/services/rag_query.py`

```python
"""
RAG Query Engine - Semantic search with context assembly.

Orchestrates embedding generation and vector search.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from .embeddings import EmbeddingService
from .vector_store import VectorStoreService, ContentDocument, SearchResult


class RAGQuery(BaseModel):
    """Input query for RAG system."""
    query: str
    n_results: int = Field(default=10, ge=1, le=100)
    platform_filter: Optional[str] = None
    author_filter: Optional[str] = None
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGResult(BaseModel):
    """Result from RAG query."""
    query: str
    results: List[SearchResult]
    context_assembled: str
    total_results: int
    query_cost_usd: float
    processing_time_seconds: float


class ContentIngestionResult(BaseModel):
    """Result from content ingestion."""
    documents_processed: int
    embeddings_generated: int
    total_tokens: int
    total_cost_usd: float
    processing_time_seconds: float
    document_ids: List[str]


class RAGQueryEngine:
    """
    RAG Query Engine for semantic content retrieval.

    Features:
    - Ingest content with automatic embedding generation
    - Semantic search across all platforms
    - Context assembly for LLM prompts
    - Cost tracking and optimization
    - Cross-platform pattern detection
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStoreService] = None
    ):
        """
        Initialize RAG engine.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: Service for vector storage
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    async def ingest_content(
        self,
        documents: List[ContentDocument]
    ) -> ContentIngestionResult:
        """
        Ingest content documents into vector store.

        Generates embeddings and stores in ChromaDB.

        Args:
            documents: List of content documents to ingest

        Returns:
            Ingestion result with cost and timing info
        """
        import time
        start_time = time.time()

        if not documents:
            return ContentIngestionResult(
                documents_processed=0,
                embeddings_generated=0,
                total_tokens=0,
                total_cost_usd=0.0,
                processing_time_seconds=0.0,
                document_ids=[]
            )

        # Generate embeddings for all content
        texts = [doc.content for doc in documents]
        batch_result = await self.embedding_service.embed_batch(texts)

        # Store in vector database
        document_ids = self.vector_store.add_documents_batch(
            documents=documents,
            embeddings=batch_result.embeddings
        )

        processing_time = time.time() - start_time

        return ContentIngestionResult(
            documents_processed=len(documents),
            embeddings_generated=len(batch_result.embeddings),
            total_tokens=batch_result.total_tokens,
            total_cost_usd=batch_result.total_cost_usd,
            processing_time_seconds=processing_time,
            document_ids=document_ids
        )

    async def query(self, rag_query: RAGQuery) -> RAGResult:
        """
        Execute semantic search query.

        Args:
            rag_query: Query parameters

        Returns:
            RAG result with matched content and context
        """
        import time
        start_time = time.time()

        # Generate embedding for query
        query_result = await self.embedding_service.embed_single(rag_query.query)

        # Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_result.embedding,
            n_results=rag_query.n_results,
            platform_filter=rag_query.platform_filter,
            author_filter=rag_query.author_filter
        )

        # Filter by minimum similarity
        if rag_query.min_similarity > 0:
            search_results = [
                r for r in search_results
                if r.similarity >= rag_query.min_similarity
            ]

        # Assemble context for LLM
        context = self._assemble_context(search_results)

        processing_time = time.time() - start_time

        return RAGResult(
            query=rag_query.query,
            results=search_results,
            context_assembled=context,
            total_results=len(search_results),
            query_cost_usd=query_result.cost_usd,
            processing_time_seconds=processing_time
        )

    def _assemble_context(self, results: List[SearchResult]) -> str:
        """
        Assemble search results into context string for LLM.

        Args:
            results: List of search results

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant content found."

        context_parts = []

        for i, result in enumerate(results, 1):
            part = f"""
--- Result {i} (Similarity: {result.similarity:.3f}) ---
Platform: {result.platform}
Author: {result.author_name}
Source: {result.source_url}

Content:
{result.content}
"""
            context_parts.append(part.strip())

        return "\n\n".join(context_parts)

    async def find_similar_content(
        self,
        content: str,
        n_results: int = 5,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """
        Find content similar to given text.

        Useful for detecting cross-platform elaboration patterns.

        Args:
            content: Content to find similar items for
            n_results: Number of results
            exclude_self: Whether to exclude exact matches

        Returns:
            List of similar content
        """
        # Get extra results if excluding self
        fetch_n = n_results + 1 if exclude_self else n_results

        query_result = await self.embedding_service.embed_single(content)

        results = self.vector_store.search(
            query_embedding=query_result.embedding,
            n_results=fetch_n
        )

        # Filter out exact matches if requested
        if exclude_self:
            results = [
                r for r in results
                if r.similarity < 0.99  # Not exact match
            ][:n_results]

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get combined statistics from all services.

        Returns:
            Dictionary with embedding costs and vector store stats
        """
        return {
            "embedding_costs": self.embedding_service.get_cost_summary(),
            "vector_store": self.vector_store.get_collection_stats(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def detect_cross_platform_patterns(
        self,
        author_id: str,
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Detect content that appears across multiple platforms.

        Identifies Dan Koe-style elaboration patterns:
        Tweet -> Newsletter -> YouTube video

        Args:
            author_id: Author to analyze
            similarity_threshold: Minimum similarity to consider related

        Returns:
            List of pattern clusters
        """
        # Get all content for author
        all_results = self.vector_store.search(
            query_embedding=[0.0] * 1536,  # Dummy query
            n_results=1000,  # Get all
            author_filter=author_id
        )

        if not all_results:
            return []

        # Group by platform
        by_platform = {}
        for result in all_results:
            platform = result.platform
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(result)

        # Find cross-platform similarities
        patterns = []
        checked = set()

        for platform1, items1 in by_platform.items():
            for item1 in items1:
                if item1.id in checked:
                    continue

                cluster = {"primary": item1, "related": []}

                # Find similar items in other platforms
                similar = await self.find_similar_content(
                    item1.content,
                    n_results=20
                )

                for sim_item in similar:
                    if (sim_item.platform != platform1 and
                        sim_item.similarity >= similarity_threshold and
                        sim_item.id not in checked):

                        cluster["related"].append(sim_item)
                        checked.add(sim_item.id)

                if cluster["related"]:
                    patterns.append(cluster)
                    checked.add(item1.id)

        return patterns
```

---

## Dependencies

Add to `backend/pyproject.toml`:

```toml
[project]
name = "unified-scraper-backend"
version = "0.1.0"
description = "Multi-platform content intelligence engine"
requires-python = ">=3.11"
dependencies = [
    "chromadb>=0.4.22",
    "openai>=1.12.0",
    "tiktoken>=0.6.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]
```

---

## Environment Variables

Create `.env` file in project root:

```bash
# OpenAI API Key (Required)
OPENAI_API_KEY=sk-your-key-here

# ChromaDB Configuration (Optional)
CHROMADB_PERSIST_DIR=data/chromadb

# Cost Limits (Optional)
MAX_EMBEDDING_COST_PER_SESSION=1.00  # USD
```

---

## Success Criteria

### Test 1: Batch Embedding Performance

**Goal**: Embed 100 items in less than 10 seconds

```bash
# Create test script: backend/tests/test_embedding_performance.py
import asyncio
import time
from services.embeddings import EmbeddingService

async def test_batch_performance():
    service = EmbeddingService()

    # Generate 100 test texts
    texts = [f"This is test document number {i} with some content about {['focus', 'productivity', 'creativity'][i % 3]}" for i in range(100)]

    start = time.time()
    result = await service.embed_batch(texts)
    elapsed = time.time() - start

    print(f"Embedded {result.items_processed} items")
    print(f"Total tokens: {result.total_tokens}")
    print(f"Total cost: ${result.total_cost_usd:.6f}")
    print(f"Processing time: {elapsed:.2f} seconds")

    assert elapsed < 10.0, f"Too slow: {elapsed:.2f}s"
    assert len(result.embeddings) == 100
    assert len(result.embeddings[0]) == 1536

asyncio.run(test_batch_performance())
```

**Run**:
```bash
cd backend
source .venv/bin/activate
python tests/test_embedding_performance.py
```

**Expected Output**:
```
Embedded 100 items
Total tokens: ~15000
Total cost: $0.000300
Processing time: 3.45 seconds
```

---

### Test 2: Vector Store CRUD Operations

```bash
# Create test script: backend/tests/test_vector_store.py
import asyncio
from datetime import datetime, timezone
from services.vector_store import VectorStoreService, ContentDocument
from services.embeddings import EmbeddingService

async def test_vector_store():
    vs = VectorStoreService(persist_directory="data/chromadb_test")
    es = EmbeddingService()

    # Create test document
    doc = ContentDocument(
        content="Focus is the new IQ. In a distracted world, attention is your competitive advantage.",
        platform="twitter",
        source_url="https://twitter.com/dankoe/status/123456",
        author_id="dankoe",
        author_name="Dan Koe",
        metrics={"likes": 1500, "retweets": 300}
    )

    # Generate embedding
    embed_result = await es.embed_single(doc.content)

    # Store document
    doc_id = vs.add_document(doc, embed_result.embedding)
    print(f"Stored document: {doc_id}")

    # Retrieve document
    retrieved = vs.get_document(doc_id)
    assert retrieved is not None
    assert retrieved["metadata"]["platform"] == "twitter"
    print(f"Retrieved: {retrieved['metadata']['author_name']}")

    # Search for similar content
    query_text = "attention and focus in the digital age"
    query_embed = await es.embed_single(query_text)
    results = vs.search(query_embed.embedding, n_results=5)

    print(f"Search results: {len(results)}")
    for r in results:
        print(f"  - {r.author_name}: {r.similarity:.3f}")

    # Get stats
    stats = vs.get_collection_stats()
    print(f"Total documents: {stats['total_documents']}")

    # Cleanup
    vs.reset_collection()
    print("Test passed!")

asyncio.run(test_vector_store())
```

---

### Test 3: RAG Query Engine

```bash
# Create test script: backend/tests/test_rag_engine.py
import asyncio
from datetime import datetime, timezone
from services.rag_query import RAGQueryEngine, RAGQuery
from services.vector_store import ContentDocument

async def test_rag_engine():
    engine = RAGQueryEngine()

    # Create sample documents
    docs = [
        ContentDocument(
            content="Focus is the new IQ. In a world of infinite distractions, your attention is your competitive advantage.",
            platform="twitter",
            source_url="https://twitter.com/dankoe/1",
            author_id="dankoe",
            author_name="Dan Koe"
        ),
        ContentDocument(
            content="Deep work requires eliminating shallow work. Block 2-4 hours of uninterrupted time each day.",
            platform="youtube",
            source_url="https://youtube.com/watch?v=abc123",
            author_id="calnewport",
            author_name="Cal Newport"
        ),
        ContentDocument(
            content="The focusing question: What's the ONE thing I can do such that by doing it everything else becomes easier?",
            platform="reddit",
            source_url="https://reddit.com/r/productivity/123",
            author_id="garykeller",
            author_name="Gary Keller"
        )
    ]

    # Ingest content
    print("Ingesting content...")
    ingest_result = await engine.ingest_content(docs)
    print(f"Processed: {ingest_result.documents_processed} docs")
    print(f"Cost: ${ingest_result.total_cost_usd:.6f}")
    print(f"Time: {ingest_result.processing_time_seconds:.2f}s")

    # Query
    print("\nQuerying: 'focus systems for knowledge workers'")
    query = RAGQuery(
        query="focus systems for knowledge workers",
        n_results=3
    )
    result = await engine.query(query)

    print(f"Found {result.total_results} results")
    for r in result.results:
        print(f"  - [{r.platform}] {r.author_name}: {r.similarity:.3f}")

    print(f"\nAssembled context:\n{result.context_assembled[:500]}...")

    # Get stats
    stats = engine.get_stats()
    print(f"\nTotal embedding cost: ${stats['embedding_costs']['total_cost_usd']:.6f}")

    print("\nRAG engine test passed!")

asyncio.run(test_rag_engine())
```

---

### Test 4: Cost Tracking Accuracy

```bash
# Create test script: backend/tests/test_cost_tracking.py
import asyncio
from services.embeddings import EmbeddingService

async def test_cost_tracking():
    service = EmbeddingService()

    # Known token counts
    test_cases = [
        ("Hello world", 2),  # ~2 tokens
        ("The quick brown fox jumps over the lazy dog", 9),  # ~9 tokens
        ("Focus " * 100, 200),  # ~200 tokens
    ]

    for text, expected_approx in test_cases:
        result = await service.embed_single(text)
        print(f"Text: '{text[:30]}...'")
        print(f"  Tokens: {result.tokens} (expected ~{expected_approx})")
        print(f"  Cost: ${result.cost_usd:.8f}")

    # Check cumulative tracking
    summary = service.get_cost_summary()
    print(f"\nCumulative stats:")
    print(f"  Total tokens: {summary['total_tokens']}")
    print(f"  Total cost: ${summary['total_cost_usd']:.6f}")
    print(f"  Requests: {summary['total_requests']}")

    # Verify cost calculation
    expected_cost = (summary['total_tokens'] / 1000) * 0.00002
    assert abs(summary['total_cost_usd'] - expected_cost) < 0.000001

    print("\nCost tracking accurate!")

asyncio.run(test_cost_tracking())
```

---

## Error Handling Patterns

### 1. Rate Limiting (OpenAI)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class EmbeddingService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def _call_openai(self, texts):
        # API call with retry logic
        pass
```

### 2. ChromaDB Connection Errors

```python
class VectorStoreService:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(...)
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB: {e}")
```

### 3. Token Limit Exceeded

```python
def embed_single(self, text):
    if self.count_tokens(text) > self.MAX_TOKENS:
        if self.auto_truncate:
            text = self.truncate_text(text)
        else:
            raise TokenLimitError(f"Text exceeds {self.MAX_TOKENS} tokens")
```

### 4. Cost Budget Exceeded

```python
class CostBudgetExceededError(Exception):
    pass

async def embed_batch(self, texts):
    estimated_cost = self.estimate_cost(texts)
    if self.cost_tracker.cost_usd + estimated_cost > self.max_budget:
        raise CostBudgetExceededError(
            f"Estimated cost ${estimated_cost:.4f} would exceed budget"
        )
```

---

## Performance Optimization

### 1. Batch Processing

Always prefer `embed_batch()` over multiple `embed_single()` calls:
- Reduces API calls (100 items = 1 call vs 100 calls)
- Lower latency (network overhead once)
- Automatic batching respects OpenAI limits

### 2. ChromaDB Indexing

```python
# Use HNSW index (default) for fast approximate nearest neighbor
self.collection = self.client.create_collection(
    name="content",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity
)
```

### 3. Memory Management

```python
# Stream large batches instead of loading all into memory
async def ingest_large_batch(self, documents, batch_size=100):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await self.ingest_content(batch)
        # Allow garbage collection
        await asyncio.sleep(0.1)
```

---

## Integration Points

### With AGENT EPSILON (Twitter Scraper)

```python
# In Twitter scraper after fetching tweets
from services.rag_query import RAGQueryEngine
from services.vector_store import ContentDocument

engine = RAGQueryEngine()

# Convert tweets to documents
docs = [
    ContentDocument(
        content=tweet.text,
        platform="twitter",
        source_url=tweet.url,
        author_id=tweet.author_id,
        author_name=tweet.author_username,
        metrics={"likes": tweet.likes, "retweets": tweet.retweets}
    )
    for tweet in scraped_tweets
]

# Ingest into RAG
result = await engine.ingest_content(docs)
```

### With AGENT ETA (FastAPI)

```python
# In FastAPI route
@router.post("/query/rag")
async def query_rag(query: RAGQuery):
    engine = RAGQueryEngine()
    result = await engine.query(query)
    return result
```

---

## Deployment Checklist

1. [ ] OpenAI API key configured in `.env`
2. [ ] `data/chromadb/` directory created with write permissions
3. [ ] Dependencies installed: `uv pip install chromadb openai tiktoken pydantic`
4. [ ] Batch embedding test passes (<10 seconds for 100 items)
5. [ ] Vector store persistence verified (survives restart)
6. [ ] Cost tracking matches OpenAI dashboard
7. [ ] Search returns relevant results (similarity > 0.7)
8. [ ] Context assembly produces coherent output

---

## Common Pitfalls to Avoid

1. **Not truncating long content**: YouTube transcripts can exceed 8K tokens
2. **Ignoring API costs**: Track every embedding generation
3. **Using wrong similarity metric**: ChromaDB defaults to L2, use cosine
4. **Not persisting ChromaDB**: In-memory collections lost on restart
5. **Blocking I/O in async context**: Always use `asyncio` versions
6. **Missing metadata**: Store platform, author, URL for filtering

---

## Next Steps After Implementation

1. **Test with real data**: Scrape 100 @dankoe tweets and ingest
2. **Validate search quality**: Query "focus" and verify relevance
3. **Monitor costs**: Track cumulative spending in logs
4. **Optimize batching**: Find ideal batch size for your use case
5. **Add caching**: Cache frequent queries to reduce embedding costs

---

*Agent ZETA - Vector Intelligence Layer*
*Cost-aware, semantically-rich content retrieval*
