"""
Local Vector Database Service using LanceDB and Sentence Transformers

This service provides FREE, local semantic search without requiring OpenAI API keys.

Features:
- LanceDB: Local, serverless vector database
- Sentence Transformers: Free, local embedding generation (all-MiniLM-L6-v2)
- 384-dimensional embeddings (smaller, faster than OpenAI's 1536)
- Cosine similarity search
- Automatic embedding generation for database content

Architecture:
- LAMBDA: Local embedding generation (sentence-transformers)
- THETA: Vector storage and retrieval (LanceDB)
- MU: Integration with existing PostgreSQL content database

Performance:
- Embedding generation: ~50-100 texts/second on CPU
- Search latency: <10ms for 10K vectors
- Storage: ~1.5KB per vector (384 dims)
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import lancedb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class LocalVectorDBService:
    """
    Local vector database service for semantic search.

    Uses:
    - LanceDB for vector storage (local, no server required)
    - Sentence Transformers for embeddings (free, runs on CPU/GPU)
    - all-MiniLM-L6-v2 model (384 dimensions, 80MB download)

    This is a cost-free alternative to OpenAI embeddings + ChromaDB.
    """

    def __init__(
        self,
        db_path: str = "./data/lancedb",
        table_name: str = "content_vectors",
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """
        Initialize local vector database service.

        Args:
            db_path: Path to LanceDB database directory
            table_name: Name of the vector table
            model_name: Sentence transformer model name
            device: Device for model inference ('cpu', 'cuda', or None for auto)
        """
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.model_name = model_name

        # Create database directory if it doesn't exist
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize LanceDB connection
        self.db = lancedb.connect(str(self.db_path))

        # Initialize embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        logger.info(f"✓ Local vector DB initialized")
        logger.info(f"  - Database: {self.db_path}")
        logger.info(f"  - Model: {model_name}")
        logger.info(f"  - Dimensions: {self.embedding_dim}")
        logger.info(f"  - Device: {self.model.device}")

        # Table will be created on first insert
        self.table = None

    def _get_or_create_table(self):
        """Get existing table or prepare for creation."""
        try:
            self.table = self.db.open_table(self.table_name)
            logger.info(f"Opened existing table: {self.table_name} ({self.count()} vectors)")
        except Exception:
            # Table doesn't exist yet, will be created on first insert
            logger.info(f"Table '{self.table_name}' will be created on first insert")
            self.table = None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector (384 dimensions)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=32,
        )
        return [emb.tolist() for emb in embeddings]

    def add_content(
        self,
        content_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Add content to vector database.

        Args:
            content_id: Unique content identifier
            text: Text content
            metadata: Optional metadata (platform, author, source, subject, etc.)
            embedding: Optional pre-computed embedding (will generate if None)
        """
        # Generate embedding if not provided
        if embedding is None:
            embedding = self.generate_embedding(text)

        # Prepare record
        record = {
            "id": content_id,
            "text": text,
            "vector": embedding,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        # Create table on first insert
        if self.table is None:
            self.table = self.db.create_table(self.table_name, data=[record])
            logger.info(f"Created table: {self.table_name}")
        else:
            # Add to existing table
            self.table.add([record])

    def add_content_batch(
        self,
        content_items: List[Dict[str, Any]],
        generate_embeddings: bool = True,
    ) -> int:
        """
        Add multiple content items in batch.

        Args:
            content_items: List of content dicts with keys:
                - id: Unique identifier
                - text: Text content
                - metadata: Optional metadata dict
                - vector: Optional pre-computed embedding
            generate_embeddings: Whether to generate embeddings for items without them

        Returns:
            Number of items added
        """
        # Generate embeddings for items that don't have them
        if generate_embeddings:
            texts_to_embed = []
            indices_to_embed = []

            for i, item in enumerate(content_items):
                if "vector" not in item or item["vector"] is None:
                    texts_to_embed.append(item["text"])
                    indices_to_embed.append(i)

            if texts_to_embed:
                logger.info(f"Generating embeddings for {len(texts_to_embed)} items...")
                embeddings = self.generate_embeddings_batch(texts_to_embed)

                for idx, embedding in zip(indices_to_embed, embeddings):
                    content_items[idx]["vector"] = embedding

        # Prepare records
        records = []
        for item in content_items:
            record = {
                "id": item["id"],
                "text": item["text"],
                "vector": item["vector"],
                "metadata": item.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
            }
            records.append(record)

        # Create or append to table
        if self.table is None:
            self.table = self.db.create_table(self.table_name, data=records)
            logger.info(f"Created table: {self.table_name} with {len(records)} records")
        else:
            self.table.add(records)
            logger.info(f"Added {len(records)} records to table")

        return len(records)

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar content.

        Args:
            query: Search query text
            limit: Maximum number of results
            filter_metadata: Optional metadata filters (e.g., {"platform": "twitter"})

        Returns:
            List of results with id, text, metadata, and similarity score
        """
        if self.table is None:
            self._get_or_create_table()

        if self.table is None:
            logger.warning("No table exists yet - returning empty results")
            return []

        # Generate query embedding
        query_embedding = self.generate_embedding(query)

        # Search with LanceDB
        search_query = self.table.search(query_embedding).limit(limit)

        # Apply metadata filters if provided
        if filter_metadata:
            # LanceDB supports SQL-like filters
            filter_conditions = []
            for key, value in filter_metadata.items():
                filter_conditions.append(f"metadata.{key} = '{value}'")

            if filter_conditions:
                filter_str = " AND ".join(filter_conditions)
                search_query = search_query.where(filter_str)

        # Execute search
        results = search_query.to_list()

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "text": result["text"],
                "metadata": result.get("metadata", {}),
                "similarity_score": 1.0 - result["_distance"],  # Convert distance to similarity
                "created_at": result.get("created_at"),
            })

        return formatted_results

    def search_by_embedding(
        self,
        query_embedding: List[float],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search using pre-computed embedding vector.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results

        Returns:
            List of results
        """
        if self.table is None:
            self._get_or_create_table()

        if self.table is None:
            return []

        results = self.table.search(query_embedding).limit(limit).to_list()

        return [
            {
                "id": r["id"],
                "text": r["text"],
                "metadata": r.get("metadata", {}),
                "similarity_score": 1.0 - r["_distance"],
                "created_at": r.get("created_at"),
            }
            for r in results
        ]

    def get_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get content by ID.

        Args:
            content_id: Content identifier

        Returns:
            Content dict or None if not found
        """
        if self.table is None:
            self._get_or_create_table()

        if self.table is None:
            return None

        results = self.table.search().where(f"id = '{content_id}'").limit(1).to_list()

        if not results:
            return None

        result = results[0]
        return {
            "id": result["id"],
            "text": result["text"],
            "metadata": result.get("metadata", {}),
            "vector": result["vector"],
            "created_at": result.get("created_at"),
        }

    def delete(self, content_id: str) -> bool:
        """
        Delete content by ID.

        Args:
            content_id: Content identifier

        Returns:
            True if deleted, False if not found
        """
        if self.table is None:
            self._get_or_create_table()

        if self.table is None:
            return False

        # LanceDB delete by filter
        self.table.delete(f"id = '{content_id}'")
        return True

    def count(self) -> int:
        """
        Get total number of vectors in database.

        Returns:
            Vector count
        """
        if self.table is None:
            self._get_or_create_table()

        if self.table is None:
            return 0

        return self.table.count_rows()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics dict with counts, storage size, etc.
        """
        if self.table is None:
            self._get_or_create_table()

        total_vectors = self.count()

        # Calculate approximate storage size
        # Each vector: 384 dims * 4 bytes (float32) = 1536 bytes
        # Plus metadata overhead ~500 bytes per record
        approx_bytes_per_record = (self.embedding_dim * 4) + 500
        approx_storage_mb = (total_vectors * approx_bytes_per_record) / (1024 * 1024)

        # Get database directory size
        db_size_bytes = sum(
            f.stat().st_size for f in self.db_path.rglob("*") if f.is_file()
        )
        db_size_mb = db_size_bytes / (1024 * 1024)

        return {
            "total_vectors": total_vectors,
            "embedding_dimensions": self.embedding_dim,
            "model": self.model_name,
            "device": str(self.model.device),
            "approx_storage_mb": round(approx_storage_mb, 2),
            "actual_storage_mb": round(db_size_mb, 2),
            "db_path": str(self.db_path),
            "table_name": self.table_name,
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Health check for vector database service.

        Returns:
            Health status dict
        """
        try:
            # Test embedding generation
            start = time.time()
            test_embedding = self.generate_embedding("test")
            embedding_time_ms = (time.time() - start) * 1000

            # Test search if table exists
            search_time_ms = None
            if self.table is not None and self.count() > 0:
                start = time.time()
                self.search("test", limit=5)
                search_time_ms = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "model": self.model_name,
                "embedding_dim": self.embedding_dim,
                "total_vectors": self.count(),
                "embedding_time_ms": round(embedding_time_ms, 2),
                "search_time_ms": round(search_time_ms, 2) if search_time_ms else None,
                "device": str(self.model.device),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# Global service instance
_vector_db_service: Optional[LocalVectorDBService] = None


def get_vector_db_service(
    db_path: Optional[str] = None,
    force_recreate: bool = False,
) -> LocalVectorDBService:
    """
    Get or create global vector database service instance.

    Args:
        db_path: Optional custom database path
        force_recreate: Force recreation of service instance

    Returns:
        LocalVectorDBService instance
    """
    global _vector_db_service

    if _vector_db_service is None or force_recreate:
        if db_path is None:
            db_path = os.getenv("VECTOR_DB_PATH", "./data/lancedb")

        _vector_db_service = LocalVectorDBService(db_path=db_path)

    return _vector_db_service
