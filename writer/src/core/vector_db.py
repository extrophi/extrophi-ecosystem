"""
Vector database management using Qdrant.

This module provides a comprehensive vector search solution with:
    - High-performance similarity search
    - Multi-tenant data isolation
    - Metadata filtering
    - Batch operations
    - Collection management
    - Async/await patterns
    - Connection pooling
    - Error handling and retries

Qdrant is a vector similarity search engine that provides production-ready
service with extended filtering support.

Example:
    Basic vector operations:
        
        from src.core.vector_db import vector_manager
        
        # Create collection
        await vector_manager.create_collection(
            "documents",
            vector_size=1536,  # OpenAI ada-002 embeddings
            on_disk=True
        )
        
        # Insert vectors
        ids = await vector_manager.upsert(
            "documents",
            vectors=embeddings,
            payloads=[{"text": doc, "user_id": 123} for doc in documents]
        )
        
        # Search similar vectors
        results = await vector_manager.search(
            "documents",
            query_vector=query_embedding,
            limit=10,
            score_threshold=0.7
        )

Note:
    All operations support multi-tenancy through automatic filtering
    when tenant_id is provided.
"""

# Standard library imports
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Tuple, Union, TypeVar, Generic,
    AsyncGenerator, Callable, Coroutine
)
from uuid import uuid4

# Third-party imports
import numpy as np
from pydantic import BaseModel, Field, validator
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, MatchText, MatchAny, Range, GeoBoundingBox, GeoRadius,
    CollectionStatus, UpdateStatus, OptimizersConfigDiff,
    CollectionInfo, SearchRequest, SearchParams, ScoredPoint,
    CountResult, UpdateResult, PointsList, PayloadSchemaType,
    PayloadIndexInfo, SparseVectorParams,
    QuantizationConfig, ScalarQuantization, ProductQuantization,
    BinaryQuantization, RecommendRequest, Record
)

# Local application imports
from src.core.config import settings

# Type variables
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_VECTOR_SIZE = 1536  # OpenAI ada-002 embeddings
DEFAULT_DISTANCE = Distance.COSINE
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_SCORE_THRESHOLD = 0.0
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 0.5


class VectorMetric(str, Enum):
    """Supported vector similarity metrics."""
    COSINE = "Cosine"
    EUCLIDEAN = "Euclid"
    DOT_PRODUCT = "Dot"
    MANHATTAN = "Manhattan"


@dataclass
class SearchResult:
    """
    Vector search result with metadata.
    
    Attributes:
        id: Point ID
        score: Similarity score
        payload: Associated metadata
        vector: Optional vector data
    """
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if result has high confidence score (>0.8)."""
        return self.score > 0.8


@dataclass
class CollectionConfig:
    """
    Collection configuration parameters.
    
    Attributes:
        name: Collection name
        vector_size: Dimension of vectors
        distance: Distance metric
        on_disk: Store vectors on disk
        quantization: Optional quantization config
        optimizers: Optional optimizer config
    """
    name: str
    vector_size: int = DEFAULT_VECTOR_SIZE
    distance: Union[Distance, VectorMetric] = DEFAULT_DISTANCE
    on_disk: bool = False
    quantization: Optional[QuantizationConfig] = None
    optimizers: Optional[OptimizersConfigDiff] = None
    shard_number: int = 1
    replication_factor: int = 1
    write_consistency_factor: int = 1
    
    def __post_init__(self):
        """Convert string metrics to Distance enum."""
        if isinstance(self.distance, str):
            metric_map = {
                VectorMetric.COSINE: Distance.COSINE,
                VectorMetric.EUCLIDEAN: Distance.EUCLID,
                VectorMetric.DOT_PRODUCT: Distance.DOT,
                VectorMetric.MANHATTAN: Distance.MANHATTAN,
            }
            self.distance = metric_map.get(self.distance, Distance.COSINE)


class VectorFilter(BaseModel):
    """
    Advanced filter builder for vector searches.
    
    This class provides a fluent interface for building complex filters.
    """
    must: List[FieldCondition] = Field(default_factory=list)
    should: List[FieldCondition] = Field(default_factory=list)
    must_not: List[FieldCondition] = Field(default_factory=list)
    
    def match(self, key: str, value: Any) -> "VectorFilter":
        """Add exact match condition."""
        self.must.append(
            FieldCondition(key=key, match=MatchValue(value=value))
        )
        return self
    
    def match_text(self, key: str, text: str) -> "VectorFilter":
        """Add text match condition."""
        self.must.append(
            FieldCondition(key=key, match=MatchText(text=text))
        )
        return self
    
    def match_any(self, key: str, values: List[Any]) -> "VectorFilter":
        """Add match any condition."""
        self.must.append(
            FieldCondition(key=key, match=MatchAny(any=values))
        )
        return self
    
    def range(self, key: str, gte: Optional[float] = None, 
              lte: Optional[float] = None) -> "VectorFilter":
        """Add range condition."""
        self.must.append(
            FieldCondition(
                key=key,
                range=Range(gte=gte, lte=lte)
            )
        )
        return self
    
    def geo_radius(self, key: str, center: Tuple[float, float], 
                   radius: float) -> "VectorFilter":
        """Add geo radius condition."""
        self.must.append(
            FieldCondition(
                key=key,
                geo_radius=GeoRadius(
                    center={"lat": center[0], "lon": center[1]},
                    radius=radius
                )
            )
        )
        return self
    
    def exclude(self, key: str, value: Any) -> "VectorFilter":
        """Add exclusion condition."""
        self.must_not.append(
            FieldCondition(key=key, match=MatchValue(value=value))
        )
        return self
    
    def build(self) -> Optional[Filter]:
        """Build the final Filter object."""
        if not any([self.must, self.should, self.must_not]):
            return None
        
        return Filter(
            must=self.must or None,
            should=self.should or None,
            must_not=self.must_not or None
        )


class VectorManager:
    """
    Async vector database manager with advanced features.
    
    This class provides high-level operations for vector similarity search
    with support for multi-tenancy, batching, and error handling.
    
    Attributes:
        client: Qdrant client instance
        async_client: Async Qdrant client instance
        collections: Cache of collection configurations
    """
    
    def __init__(self):
        """Initialize vector manager with configuration."""
        self.client: Optional[QdrantClient] = None
        self.async_client: Optional[AsyncQdrantClient] = None
        self.collections: Dict[str, CollectionConfig] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize Qdrant clients.
        
        Creates both sync and async clients for maximum flexibility.
        """
        if self._initialized:
            return
        
        try:
            if settings.QDRANT_USE_MEMORY:
                # In-memory mode for development
                self.client = QdrantClient(":memory:")
                self.async_client = AsyncQdrantClient(":memory:")
                logger.info("Initialized Qdrant in memory mode")
            else:
                # Production mode with real Qdrant server
                client_kwargs = {
                    "host": settings.QDRANT_HOST,
                    "port": settings.QDRANT_PORT,
                    "api_key": settings.QDRANT_API_KEY,
                    "timeout": 30,
                }
                
                self.client = QdrantClient(**client_kwargs)
                self.async_client = AsyncQdrantClient(**client_kwargs)
                
                # Test connection
                await self.async_client.get_collections()
                logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise ConnectionError(f"Qdrant initialization failed: {e}")
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: Union[Distance, VectorMetric] = DEFAULT_DISTANCE,
        on_disk: bool = False,
        force_recreate: bool = False,
        **kwargs
    ) -> CollectionInfo:
        """
        Create or update a vector collection.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric for similarity
            on_disk: Store vectors on disk for large collections
            force_recreate: Delete and recreate if exists
            **kwargs: Additional collection configuration
            
        Returns:
            Collection information
            
        Raises:
            ValueError: If collection exists and force_recreate is False
        """
        await self.initialize()
        
        # Create collection config
        config = CollectionConfig(
            name=collection_name,
            vector_size=vector_size,
            distance=distance,
            on_disk=on_disk,
            **kwargs
        )
        
        try:
            # Check if collection exists
            collections = await self.async_client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if exists:
                if force_recreate:
                    await self.async_client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                else:
                    # Update collection config cache
                    self.collections[collection_name] = config
                    return await self.async_client.get_collection(collection_name)
            
            # Create collection
            await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config.vector_size,
                    distance=config.distance,
                    on_disk=config.on_disk
                ),
                shard_number=config.shard_number,
                replication_factor=config.replication_factor,
                write_consistency_factor=config.write_consistency_factor,
                optimizers_config=config.optimizers,
                quantization_config=config.quantization
            )
            
            # Cache configuration
            self.collections[collection_name] = config
            logger.info(f"Created collection: {collection_name}")
            
            return await self.async_client.get_collection(collection_name)
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    async def upsert(
        self,
        collection_name: str,
        vectors: Union[List[List[float]], np.ndarray],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        batch_size: int = BATCH_SIZE,
        wait: bool = True
    ) -> List[str]:
        """
        Insert or update vectors with metadata.
        
        Args:
            collection_name: Target collection
            vectors: Vector embeddings
            payloads: Metadata for each vector
            ids: Optional IDs (auto-generated if not provided)
            tenant_id: Optional tenant identifier
            batch_size: Batch size for large uploads
            wait: Wait for operation completion
            
        Returns:
            List of point IDs
            
        Raises:
            ValueError: If vectors and payloads have different lengths
        """
        await self.initialize()
        
        # Convert numpy arrays
        if isinstance(vectors, np.ndarray):
            vectors = vectors.tolist()
        
        # Validate inputs
        if len(vectors) != len(payloads):
            raise ValueError(
                f"Vectors ({len(vectors)}) and payloads ({len(payloads)}) "
                "must have the same length"
            )
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid4()) for _ in range(len(vectors))]
        elif len(ids) != len(vectors):
            raise ValueError("IDs must match vectors length")
        
        # Add tenant ID to payloads if multi-tenant
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            for payload in payloads:
                payload["tenant_id"] = tenant_id
        
        # Process in batches
        all_ids = []
        for i in range(0, len(vectors), batch_size):
            batch_end = min(i + batch_size, len(vectors))
            batch_points = [
                PointStruct(
                    id=ids[j],
                    vector=vectors[j],
                    payload=payloads[j]
                )
                for j in range(i, batch_end)
            ]
            
            # Retry logic
            for attempt in range(MAX_RETRIES):
                try:
                    await self.async_client.upsert(
                        collection_name=collection_name,
                        points=batch_points,
                        wait=wait
                    )
                    all_ids.extend(ids[i:batch_end])
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(
                            f"Upsert failed (attempt {attempt + 1}): {e}"
                        )
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.error(f"Upsert failed after {MAX_RETRIES} attempts")
                        raise
        
        logger.info(f"Upserted {len(all_ids)} vectors to {collection_name}")
        return all_ids
    
    async def search(
        self,
        collection_name: str,
        query_vector: Union[List[float], np.ndarray],
        limit: int = DEFAULT_SEARCH_LIMIT,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        filter_dict: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        offset: int = 0
    ) -> List[SearchResult]:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            filter_dict: Metadata filters
            tenant_id: Optional tenant identifier
            with_payload: Include metadata in results
            with_vectors: Include vector data in results
            offset: Pagination offset
            
        Returns:
            List of search results sorted by similarity
        """
        await self.initialize()
        
        # Convert numpy array
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        
        # Build filter
        filter_builder = VectorFilter()
        
        # Add tenant filter
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            filter_builder.match("tenant_id", tenant_id)
        
        # Add custom filters
        if filter_dict:
            for key, value in filter_dict.items():
                if isinstance(value, dict):
                    # Range query
                    if "gte" in value or "lte" in value:
                        filter_builder.range(
                            key,
                            gte=value.get("gte"),
                            lte=value.get("lte")
                        )
                    # Geo query
                    elif "center" in value and "radius" in value:
                        filter_builder.geo_radius(
                            key,
                            center=value["center"],
                            radius=value["radius"]
                        )
                elif isinstance(value, list):
                    # Match any
                    filter_builder.match_any(key, value)
                else:
                    # Exact match
                    filter_builder.match(key, value)
        
        # Perform search
        try:
            results = await self.async_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                offset=offset,
                query_filter=filter_builder.build(),
                with_payload=with_payload,
                with_vectors=with_vectors,
                score_threshold=score_threshold
            )
            
            # Convert to SearchResult objects
            return [
                SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    payload=hit.payload if with_payload else {},
                    vector=hit.vector if with_vectors else None
                )
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            raise
    
    async def recommend(
        self,
        collection_name: str,
        positive: List[str],
        negative: Optional[List[str]] = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        filter_dict: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[SearchResult]:
        """
        Find vectors similar to positive examples and dissimilar to negative.
        
        Args:
            collection_name: Collection to search
            positive: IDs of positive examples
            negative: IDs of negative examples
            limit: Maximum results
            score_threshold: Minimum score
            filter_dict: Metadata filters
            tenant_id: Tenant identifier
            with_payload: Include metadata
            with_vectors: Include vectors
            
        Returns:
            Recommended vectors
        """
        await self.initialize()
        
        # Build filter
        filter_builder = VectorFilter()
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            filter_builder.match("tenant_id", tenant_id)
        
        if filter_dict:
            for key, value in filter_dict.items():
                filter_builder.match(key, value)
        
        # Perform recommendation
        try:
            results = await self.async_client.recommend(
                collection_name=collection_name,
                positive=positive,
                negative=negative or [],
                limit=limit,
                query_filter=filter_builder.build(),
                with_payload=with_payload,
                with_vectors=with_vectors,
                score_threshold=score_threshold
            )
            
            return [
                SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    payload=hit.payload if with_payload else {},
                    vector=hit.vector if with_vectors else None
                )
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"Recommendation failed: {e}")
            raise
    
    async def delete(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        wait: bool = True
    ) -> Optional[UpdateResult]:
        """
        Delete vectors by IDs or filter.
        
        Args:
            collection_name: Collection name
            ids: Point IDs to delete
            filter_dict: Delete by filter
            tenant_id: Tenant identifier
            wait: Wait for completion
            
        Returns:
            Update result
        """
        await self.initialize()
        
        if not ids and not filter_dict and not tenant_id:
            raise ValueError("Provide ids, filter_dict, or tenant_id")
        
        # Build filter for deletion
        if filter_dict or tenant_id:
            filter_builder = VectorFilter()
            
            if settings.ENABLE_MULTI_TENANT and tenant_id:
                filter_builder.match("tenant_id", tenant_id)
            
            if filter_dict:
                for key, value in filter_dict.items():
                    filter_builder.match(key, value)
            
            points_selector = filter_builder.build()
        else:
            points_selector = PointsList(points=ids)
        
        # Delete points
        try:
            result = await self.async_client.delete(
                collection_name=collection_name,
                points_selector=points_selector,
                wait=wait
            )
            
            logger.info(f"Deleted points from {collection_name}")
            return result
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    async def get_points(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Record]:
        """
        Retrieve specific points by IDs.
        
        Args:
            collection_name: Collection name
            ids: Point IDs
            with_payload: Include metadata
            with_vectors: Include vectors
            
        Returns:
            List of points
        """
        await self.initialize()
        
        try:
            points = await self.async_client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            return points
            
        except Exception as e:
            logger.error(f"Failed to retrieve points: {e}")
            raise
    
    async def count(
        self,
        collection_name: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        exact: bool = True
    ) -> int:
        """
        Count vectors in collection.
        
        Args:
            collection_name: Collection name
            filter_dict: Count with filter
            tenant_id: Tenant identifier
            exact: Use exact count
            
        Returns:
            Number of vectors
        """
        await self.initialize()
        
        # Build filter
        filter_builder = VectorFilter()
        
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            filter_builder.match("tenant_id", tenant_id)
        
        if filter_dict:
            for key, value in filter_dict.items():
                filter_builder.match(key, value)
        
        # Get count
        try:
            result = await self.async_client.count(
                collection_name=collection_name,
                count_filter=filter_builder.build(),
                exact=exact
            )
            return result.count
            
        except Exception as e:
            logger.error(f"Count failed: {e}")
            raise
    
    async def update_payload(
        self,
        collection_name: str,
        payload: Dict[str, Any],
        ids: Optional[List[str]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        wait: bool = True
    ) -> Optional[UpdateResult]:
        """
        Update payload for existing vectors.
        
        Args:
            collection_name: Collection name
            payload: New payload values
            ids: Point IDs to update
            filter_dict: Update by filter
            tenant_id: Tenant identifier
            wait: Wait for completion
            
        Returns:
            Update result
        """
        await self.initialize()
        
        # Build selector
        if ids:
            points_selector = PointsList(points=ids)
        else:
            filter_builder = VectorFilter()
            
            if settings.ENABLE_MULTI_TENANT and tenant_id:
                filter_builder.match("tenant_id", tenant_id)
            
            if filter_dict:
                for key, value in filter_dict.items():
                    filter_builder.match(key, value)
            
            points_selector = filter_builder.build()
        
        # Update payload
        try:
            result = await self.async_client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=points_selector,
                wait=wait
            )
            
            logger.info(f"Updated payload in {collection_name}")
            return result
            
        except Exception as e:
            logger.error(f"Payload update failed: {e}")
            raise
    
    async def create_index(
        self,
        collection_name: str,
        field_name: str,
        field_type: PayloadSchemaType = PayloadSchemaType.KEYWORD
    ) -> UpdateResult:
        """
        Create payload index for faster filtering.
        
        Args:
            collection_name: Collection name
            field_name: Field to index
            field_type: Field data type
            
        Returns:
            Update result
        """
        await self.initialize()
        
        try:
            result = await self.async_client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_type
            )
            
            logger.info(f"Created index on {field_name} in {collection_name}")
            return result
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise
    
    async def get_collection_info(
        self,
        collection_name: str
    ) -> CollectionInfo:
        """Get detailed collection information."""
        await self.initialize()
        return await self.async_client.get_collection(collection_name)
    
    async def list_collections(self) -> List[str]:
        """List all collection names."""
        await self.initialize()
        collections = await self.async_client.get_collections()
        return [c.name for c in collections.collections]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on vector database.
        
        Returns:
            Health status dictionary
        """
        try:
            await self.initialize()
            
            # Get collections
            collections = await self.list_collections()
            
            # Get basic metrics
            total_vectors = 0
            for collection in collections:
                count = await self.count(collection)
                total_vectors += count
            
            return {
                "status": "healthy",
                "connected": True,
                "collections": len(collections),
                "total_vectors": total_vectors,
                "mode": "memory" if settings.QDRANT_USE_MEMORY else "server"
            }
            
        except Exception as e:
            logger.error(f"Vector DB health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close client connections."""
        if self.async_client:
            await self.async_client.close()
        self._initialized = False
        logger.info("Closed vector database connections")


# Create singleton instance
vector_manager = VectorManager()

# Export convenience functions
create_collection = vector_manager.create_collection
upsert = vector_manager.upsert
search = vector_manager.search
recommend = vector_manager.recommend
delete = vector_manager.delete
count = vector_manager.count
update_payload = vector_manager.update_payload