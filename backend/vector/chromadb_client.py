"""ChromaDB client for vector storage and retrieval."""

import os
from typing import Any

import chromadb
from chromadb.config import Settings

CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))


class ChromaDBClient:
    """
    ChromaDB client for vector storage and semantic search.

    Features:
    - Content embedding storage (1536 dims)
    - Semantic similarity search
    - Metadata filtering
    - Collection management
    """

    def __init__(self, collection_name: str = "unified_content"):
        self.client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add_content(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add content embeddings to the collection.

        Args:
            ids: Unique content IDs
            embeddings: Vector embeddings (1536 dims)
            documents: Original text documents
            metadatas: Optional metadata dicts
        """
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas or [{}] * len(ids),
        )

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query for similar content.

        Args:
            query_embedding: Query vector (1536 dims)
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter

        Returns:
            Query results with IDs, distances, documents, metadatas
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
        )

    def get(self, ids: list[str]) -> dict[str, Any]:
        """Get content by IDs."""
        return self.collection.get(ids=ids)

    def delete(self, ids: list[str]) -> None:
        """Delete content by IDs."""
        self.collection.delete(ids=ids)

    def count(self) -> int:
        """Get total number of items in collection."""
        return self.collection.count()

    def health_check(self) -> dict[str, Any]:
        """Check ChromaDB connectivity."""
        try:
            heartbeat = self.client.heartbeat()
            return {
                "status": "ok",
                "message": "ChromaDB connected",
                "heartbeat": heartbeat,
                "collection": self.collection.name,
                "count": self.count(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
