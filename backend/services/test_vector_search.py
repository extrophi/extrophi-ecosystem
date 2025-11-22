"""
Test Local Vector Search with Sample Queries

This script tests the local vector database with specific queries
related to ultra-learning, audience building, and marketing.

Usage:
    python -m backend.services.test_vector_search

Test Queries:
    1. "How to build an audience"
    2. "Marketing frameworks"
    3. "First principles thinking"
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_db_service import get_vector_db_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_search_results(query: str, results: List[Dict[str, Any]], elapsed_ms: float):
    """Print formatted search results."""
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    print(f"Results: {len(results)} | Time: {elapsed_ms:.2f}ms\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}] Similarity: {result['similarity_score']:.4f}")
        print(f"    Platform: {result['metadata'].get('platform', 'N/A')}")
        print(f"    Source: {result['metadata'].get('source', 'N/A')}")
        print(f"    Author: {result['metadata'].get('author', 'N/A')}")

        # Print text preview (first 200 chars)
        text_preview = result['text'][:200]
        if len(result['text']) > 200:
            text_preview += "..."
        print(f"    Text: {text_preview}")
        print()


async def test_vector_search():
    """Test vector search with sample queries."""
    logger.info("Starting vector search tests...")

    # Initialize vector database service
    vector_db = get_vector_db_service()

    # Check database status
    stats = vector_db.get_statistics()
    logger.info(f"Vector database status:")
    logger.info(f"  - Total vectors: {stats['total_vectors']}")
    logger.info(f"  - Model: {stats['model']}")
    logger.info(f"  - Storage: {stats['actual_storage_mb']:.2f} MB")

    if stats['total_vectors'] == 0:
        logger.error("No vectors in database. Run populate_vector_db.py first.")
        return

    # Test queries
    test_queries = [
        "How to build an audience",
        "Marketing frameworks",
        "First principles thinking",
        "Content creation strategies",
        "Personal branding techniques",
        "Social media growth tactics",
        "Writing compelling copy",
        "Email marketing best practices",
    ]

    all_results = []
    total_time_ms = 0

    print("\n" + "=" * 80)
    print("LOCAL VECTOR SEARCH TEST RESULTS")
    print("=" * 80)

    for query in test_queries:
        # Measure search time
        start = time.time()
        results = vector_db.search(query, limit=10)
        elapsed_ms = (time.time() - start) * 1000
        total_time_ms += elapsed_ms

        # Print results
        print_search_results(query, results, elapsed_ms)

        # Store for summary
        all_results.append({
            "query": query,
            "num_results": len(results),
            "time_ms": elapsed_ms,
            "top_score": results[0]["similarity_score"] if results else 0,
        })

    # Performance summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"Total queries: {len(test_queries)}")
    print(f"Total time: {total_time_ms:.2f}ms")
    print(f"Average time per query: {total_time_ms / len(test_queries):.2f}ms")
    print(f"Queries per second: {1000 / (total_time_ms / len(test_queries)):.2f}")
    print()

    # Query breakdown
    print("Query Performance Breakdown:")
    print("-" * 80)
    for result in all_results:
        print(f"  {result['query']:<40} {result['time_ms']:>8.2f}ms | "
              f"Results: {result['num_results']:>3} | "
              f"Top Score: {result['top_score']:.4f}")

    print("\n" + "=" * 80)

    # Health check
    health = vector_db.health_check()
    print("\nHEALTH CHECK:")
    print(f"  Status: {health['status']}")
    print(f"  Model: {health['model']}")
    print(f"  Total vectors: {health['total_vectors']}")
    print(f"  Embedding time: {health['embedding_time_ms']:.2f}ms")
    print(f"  Search time: {health['search_time_ms']:.2f}ms" if health['search_time_ms'] else "  Search time: N/A")
    print(f"  Device: {health['device']}")
    print("=" * 80)


async def test_metadata_filtering():
    """Test metadata filtering capabilities."""
    logger.info("\nTesting metadata filtering...")

    vector_db = get_vector_db_service()

    print("\n" + "=" * 80)
    print("METADATA FILTERING TEST")
    print("=" * 80)

    # Test platform-specific search
    platforms = ["twitter", "youtube", "reddit", "web"]

    for platform in platforms:
        try:
            start = time.time()
            results = vector_db.search(
                "marketing strategies",
                limit=5,
                filter_metadata={"platform": platform}
            )
            elapsed_ms = (time.time() - start) * 1000

            print(f"\nPlatform: {platform}")
            print(f"Results: {len(results)} | Time: {elapsed_ms:.2f}ms")

            if results:
                print(f"Top result score: {results[0]['similarity_score']:.4f}")
            else:
                print("No results found")

        except Exception as e:
            print(f"\nPlatform: {platform}")
            print(f"Error: {str(e)}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_vector_search())
    asyncio.run(test_metadata_filtering())
