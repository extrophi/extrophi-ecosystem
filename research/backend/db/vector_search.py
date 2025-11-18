"""Vector similarity search using pgvector"""

from decimal import Decimal
from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session

def vector_similarity_search(
    db: Session,
    query_embedding: List[float],
    platform: str = None,
    min_similarity: Decimal = Decimal("0.75"),
    limit: int = 10,
) -> List[dict]:
    """Perform vector similarity search on content embeddings"""
    conditions = ["c.embedding IS NOT NULL"]
    
    if platform:
        conditions.append(f"c.platform = '{platform}'")
    
    conditions.append(f"(1 - (c.embedding <=> :embedding)) >= {min_similarity}")
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT
            c.id::text as content_id,
            c.platform,
            c.source_url,
            c.author_id,
            c.content_title,
            c.content_body,
            (1 - (c.embedding <=> :embedding))::DECIMAL(5,4) as similarity
        FROM contents c
        WHERE {where_clause}
        ORDER BY c.embedding <=> :embedding
        LIMIT :limit
    """)
    
    embedding_str = f"[{','.join(map(str, query_embedding))}]"
    result = db.execute(query, {"embedding": embedding_str, "limit": limit})
    
    return [dict(row._mapping) for row in result]
