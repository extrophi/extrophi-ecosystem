"""RAG query API endpoints."""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.vector.chromadb_client import ChromaDBClient
from backend.vector.embeddings import EmbeddingGenerator

router = APIRouter(prefix="/query", tags=["rag"])


class RAGQueryRequest(BaseModel):
    prompt: str
    n_results: int = 10
    platform_filter: Optional[str] = None
    author_filter: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    count: int


@router.post("/rag", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Semantic search across all content.

    Args:
        prompt: Natural language query
        n_results: Number of results to return
        platform_filter: Optional platform filter
        author_filter: Optional author filter

    Returns:
        Semantically similar content pieces
    """
    try:
        # Generate query embedding
        embedding_gen = EmbeddingGenerator()
        query_embedding = embedding_gen.generate(request.prompt)

        # Search ChromaDB
        chroma_client = ChromaDBClient()

        # Build metadata filter
        where_filter = None
        if request.platform_filter or request.author_filter:
            where_filter = {}
            if request.platform_filter:
                where_filter["platform"] = request.platform_filter
            if request.author_filter:
                where_filter["author_id"] = request.author_filter

        results = chroma_client.query(
            query_embedding=query_embedding,
            n_results=request.n_results,
            where=where_filter,
        )

        # Format results
        formatted_results = []
        if results.get("ids") and results["ids"][0]:
            for i, content_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "content_id": content_id,
                        "distance": results["distances"][0][i]
                        if results.get("distances")
                        else None,
                        "document": results["documents"][0][i]
                        if results.get("documents")
                        else None,
                        "metadata": results["metadatas"][0][i]
                        if results.get("metadatas")
                        else {},
                    }
                )

        return RAGQueryResponse(
            query=request.prompt,
            results=formatted_results,
            count=len(formatted_results),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def vector_health():
    """Check vector store health."""
    try:
        chroma_client = ChromaDBClient()
        return chroma_client.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e)}
