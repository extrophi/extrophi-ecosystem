"""
Populate Local Vector Database from PostgreSQL Content

This script reads content from the PostgreSQL database and indexes it
in the local LanceDB vector database for semantic search.

Usage:
    python -m backend.services.populate_vector_db

Requirements:
    - PostgreSQL database must be running and configured
    - OPENAI_API_KEY is NOT required (uses local embeddings)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.backend.db import get_db_manager, ContentCRUD, SourceCRUD
from services.vector_db_service import get_vector_db_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def populate_vector_database():
    """
    Populate vector database from PostgreSQL content.

    Process:
    1. Connect to PostgreSQL database
    2. Fetch all content entries
    3. Generate local embeddings using sentence-transformers
    4. Store vectors in LanceDB
    """
    logger.info("Starting vector database population...")

    # Initialize database connection
    db_manager = get_db_manager()

    try:
        await db_manager.connect()
        logger.info("✓ Connected to PostgreSQL database")

        # Initialize CRUD services
        content_crud = ContentCRUD(db_manager)
        source_crud = SourceCRUD(db_manager)

        # Get content statistics
        total_contents = await content_crud.count_with_embeddings()
        logger.info(f"Found {total_contents} content entries in database")

        if total_contents == 0:
            logger.warning("No content found in database. Exiting.")
            return

        # Initialize local vector database
        vector_db = get_vector_db_service()
        logger.info(f"✓ Initialized local vector database")
        logger.info(f"  - Model: {vector_db.model_name}")
        logger.info(f"  - Dimensions: {vector_db.embedding_dim}")

        # Fetch all content in batches
        batch_size = 100
        offset = 0
        total_indexed = 0

        while True:
            # Fetch batch of content
            query = """
                SELECT
                    c.id,
                    c.text_content,
                    c.content_type,
                    s.platform,
                    s.url,
                    s.title,
                    s.author,
                    s.published_at
                FROM contents c
                JOIN sources s ON c.source_id = s.id
                ORDER BY c.created_at DESC
                LIMIT $1 OFFSET $2
            """

            rows = await db_manager.fetch(query, batch_size, offset)

            if not rows:
                break

            logger.info(f"Processing batch: {offset} - {offset + len(rows)}")

            # Prepare content items for vector database
            content_items = []

            for row in rows:
                # Combine text content with metadata for richer embeddings
                text = row["text_content"]

                # Create metadata dict
                metadata = {
                    "content_type": row["content_type"],
                    "platform": row["platform"],
                    "url": row["url"],
                    "author": row.get("author"),
                    "source": row.get("title") or row["url"],
                }

                # Add subject/category if available (for ultra_learning categorization)
                # This can be enhanced with LLM-based subject classification
                if "ultra" in text.lower() or "learning" in text.lower():
                    metadata["subject"] = "ultra_learning"

                content_items.append({
                    "id": str(row["id"]),
                    "text": text,
                    "metadata": metadata,
                })

            # Batch insert into vector database
            num_added = vector_db.add_content_batch(
                content_items,
                generate_embeddings=True,
            )

            total_indexed += num_added
            logger.info(f"  ✓ Indexed {num_added} items (Total: {total_indexed})")

            offset += batch_size

        # Final statistics
        stats = vector_db.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("VECTOR DATABASE POPULATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total vectors stored: {stats['total_vectors']}")
        logger.info(f"Embedding dimensions: {stats['embedding_dimensions']}")
        logger.info(f"Storage size: {stats['actual_storage_mb']:.2f} MB")
        logger.info(f"Model: {stats['model']}")
        logger.info(f"Device: {stats['device']}")
        logger.info(f"Database path: {stats['db_path']}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error populating vector database: {e}", exc_info=True)
        raise

    finally:
        await db_manager.disconnect()
        logger.info("Disconnected from database")


if __name__ == "__main__":
    asyncio.run(populate_vector_database())
