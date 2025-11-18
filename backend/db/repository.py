"""Repository pattern for database operations with vector search support"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from backend.db.models import (
    AuthorORM,
    ContentORM,
    PatternORM,
    ResearchSessionORM,
)


class ContentRepository:
    """Repository for content CRUD operations and vector search"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        platform: str,
        source_url: str,
        author_id: str,
        content_body: str,
        content_title: Optional[str] = None,
        published_at: Optional[datetime] = None,
        metrics: Optional[Dict[str, Any]] = None,
        analysis: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentORM:
        """
        Create new content entry.

        Args:
            platform: Platform name (twitter, youtube, reddit, web)
            source_url: Unique content URL
            author_id: Author/creator ID
            content_body: Main content text
            content_title: Optional content title
            published_at: Original publication timestamp
            metrics: Engagement metrics dict
            analysis: LLM analysis results dict
            embedding: Vector embedding (1536 dims)
            metadata: Platform-specific metadata

        Returns:
            Created ContentORM instance

        Raises:
            IntegrityError: If source_url already exists
        """
        content = ContentORM(
            platform=platform,
            source_url=source_url,
            author_id=author_id,
            content_title=content_title,
            content_body=content_body,
            published_at=published_at,
            metrics=metrics or {},
            analysis=analysis or {},
            embedding=embedding,
            extra_metadata=metadata or {},
        )
        self.session.add(content)
        self.session.commit()
        self.session.refresh(content)
        return content

    def get_by_id(self, content_id: UUID) -> Optional[ContentORM]:
        """Get content by UUID"""
        return self.session.get(ContentORM, content_id)

    def get_by_url(self, source_url: str) -> Optional[ContentORM]:
        """Get content by source URL"""
        return self.session.query(ContentORM).filter_by(source_url=source_url).first()

    def list_by_platform(
        self, platform: str, limit: int = 100, offset: int = 0
    ) -> List[ContentORM]:
        """List content by platform with pagination"""
        return (
            self.session.query(ContentORM)
            .filter_by(platform=platform)
            .order_by(desc(ContentORM.scraped_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def list_by_author(
        self, author_id: str, limit: int = 100, offset: int = 0
    ) -> List[ContentORM]:
        """List content by author with pagination"""
        return (
            self.session.query(ContentORM)
            .filter_by(author_id=author_id)
            .order_by(desc(ContentORM.published_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update_embedding(self, content_id: UUID, embedding: List[float]) -> bool:
        """
        Update content embedding vector.

        Args:
            content_id: Content UUID
            embedding: Vector embedding (1536 dims)

        Returns:
            True if updated, False if not found
        """
        content = self.get_by_id(content_id)
        if not content:
            return False

        content.embedding = embedding
        self.session.commit()
        return True

    def update_analysis(self, content_id: UUID, analysis: Dict[str, Any]) -> bool:
        """
        Update content analysis results.

        Args:
            content_id: Content UUID
            analysis: LLM analysis dict

        Returns:
            True if updated, False if not found
        """
        content = self.get_by_id(content_id)
        if not content:
            return False

        content.analysis = analysis
        content.analyzed_at = datetime.utcnow()
        self.session.commit()
        return True

    def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        platform: Optional[str] = None,
        min_similarity: float = 0.7,
    ) -> List[Tuple[ContentORM, float]]:
        """
        Semantic similarity search using cosine distance.

        Args:
            query_embedding: Query vector (1536 dims)
            limit: Number of results to return
            platform: Optional platform filter
            min_similarity: Minimum cosine similarity (0.0-1.0)

        Returns:
            List of (ContentORM, similarity_score) tuples, sorted by similarity
        """
        # Convert similarity threshold to distance (cosine distance = 1 - similarity)
        max_distance = 1.0 - min_similarity

        query = select(
            ContentORM,
            (1 - ContentORM.embedding.cosine_distance(query_embedding)).label("similarity"),
        ).where(ContentORM.embedding.is_not(None))

        if platform:
            query = query.where(ContentORM.platform == platform)

        # Filter by distance and order by similarity
        query = (
            query.where(ContentORM.embedding.cosine_distance(query_embedding) <= max_distance)
            .order_by(ContentORM.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        results = self.session.execute(query).all()
        return [(row[0], float(row[1])) for row in results]

    def count_by_platform(self, platform: str) -> int:
        """
        Count total content pieces for a platform.

        Optimized: Uses COUNT(*) which is faster than count()
        """
        return (
            self.session.query(func.count(ContentORM.id))
            .filter(ContentORM.platform == platform)
            .scalar()
        )

    def count_analyzed(self) -> int:
        """
        Count content pieces with LLM analysis.

        Optimized: Uses partial index and scalar() for better performance
        """
        return (
            self.session.query(func.count(ContentORM.id))
            .filter(ContentORM.analyzed_at.is_not(None))
            .scalar()
        )

    def delete(self, content_id: UUID) -> bool:
        """Delete content by ID"""
        content = self.get_by_id(content_id)
        if not content:
            return False

        self.session.delete(content)
        self.session.commit()
        return True


class AuthorRepository:
    """Repository for author/creator operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        author_id: str,
        platform: str,
        username: str,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        follower_count: Optional[str] = None,
        following_count: Optional[str] = None,
        content_count: Optional[str] = None,
        authority_score: Optional[str] = None,
        profile_url: Optional[str] = None,
        avatar_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuthorORM:
        """Create or update author entry"""
        # Check if author exists
        existing = self.session.get(AuthorORM, author_id)
        if existing:
            # Update existing
            existing.display_name = display_name or existing.display_name
            existing.bio = bio or existing.bio
            existing.follower_count = follower_count or existing.follower_count
            existing.following_count = following_count or existing.following_count
            existing.content_count = content_count or existing.content_count
            existing.authority_score = authority_score or existing.authority_score
            existing.profile_url = profile_url or existing.profile_url
            existing.avatar_url = avatar_url or existing.avatar_url
            if metadata:
                existing.extra_metadata = metadata
            existing.last_updated = datetime.utcnow()
            self.session.commit()
            self.session.refresh(existing)
            return existing

        # Create new
        author = AuthorORM(
            id=author_id,
            platform=platform,
            username=username,
            display_name=display_name,
            bio=bio,
            follower_count=follower_count,
            following_count=following_count,
            content_count=content_count,
            authority_score=authority_score,
            profile_url=profile_url,
            avatar_url=avatar_url,
            extra_metadata=metadata or {},
        )
        self.session.add(author)
        self.session.commit()
        self.session.refresh(author)
        return author

    def get_by_id(self, author_id: str) -> Optional[AuthorORM]:
        """Get author by ID"""
        return self.session.get(AuthorORM, author_id)

    def get_by_username(self, platform: str, username: str) -> Optional[AuthorORM]:
        """Get author by platform and username"""
        return (
            self.session.query(AuthorORM)
            .filter_by(platform=platform, username=username)
            .first()
        )

    def list_by_platform(
        self, platform: str, limit: int = 100, offset: int = 0
    ) -> List[AuthorORM]:
        """List authors by platform"""
        return (
            self.session.query(AuthorORM)
            .filter_by(platform=platform)
            .order_by(desc(AuthorORM.discovered_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete(self, author_id: str) -> bool:
        """Delete author (cascades to content)"""
        author = self.get_by_id(author_id)
        if not author:
            return False

        self.session.delete(author)
        self.session.commit()
        return True


class PatternRepository:
    """Repository for pattern detection operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        author_id: str,
        pattern_type: str,
        description: str,
        content_ids: List[str],
        confidence_score: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> PatternORM:
        """Create detected pattern"""
        pattern = PatternORM(
            author_id=author_id,
            pattern_type=pattern_type,
            description=description,
            content_ids=content_ids,
            confidence_score=confidence_score,
            analysis=analysis or {},
        )
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def get_by_id(self, pattern_id: UUID) -> Optional[PatternORM]:
        """Get pattern by ID"""
        return self.session.get(PatternORM, pattern_id)

    def list_by_author(
        self, author_id: str, limit: int = 100, offset: int = 0
    ) -> List[PatternORM]:
        """List patterns for an author"""
        return (
            self.session.query(PatternORM)
            .filter_by(author_id=author_id)
            .order_by(desc(PatternORM.discovered_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def list_by_type(
        self, pattern_type: str, limit: int = 100, offset: int = 0
    ) -> List[PatternORM]:
        """List patterns by type"""
        return (
            self.session.query(PatternORM)
            .filter_by(pattern_type=pattern_type)
            .order_by(desc(PatternORM.confidence_score))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete(self, pattern_id: UUID) -> bool:
        """Delete pattern"""
        pattern = self.get_by_id(pattern_id)
        if not pattern:
            return False

        self.session.delete(pattern)
        self.session.commit()
        return True


class ResearchSessionRepository:
    """Repository for research session operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        session_name: str,
        project_brief: Optional[str] = None,
        target_authorities: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> ResearchSessionORM:
        """Create new research session"""
        session_obj = ResearchSessionORM(
            session_name=session_name,
            project_brief=project_brief,
            target_authorities=target_authorities or [],
            platforms=platforms or [],
            keywords=keywords or [],
        )
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_by_id(self, session_id: UUID) -> Optional[ResearchSessionORM]:
        """Get research session by ID"""
        return self.session.get(ResearchSessionORM, session_id)

    def update_stats(
        self,
        session_id: UUID,
        scraped: Optional[int] = None,
        analyzed: Optional[int] = None,
        patterns: Optional[int] = None,
    ) -> bool:
        """Update session statistics"""
        session_obj = self.get_by_id(session_id)
        if not session_obj:
            return False

        if scraped is not None:
            session_obj.total_pieces_scraped = str(scraped)
        if analyzed is not None:
            session_obj.total_pieces_analyzed = str(analyzed)
        if patterns is not None:
            session_obj.patterns_detected = str(patterns)

        self.session.commit()
        return True

    def update_outputs(self, session_id: UUID, outputs: Dict[str, Any]) -> bool:
        """Update generated outputs"""
        session_obj = self.get_by_id(session_id)
        if not session_obj:
            return False

        session_obj.outputs = outputs
        self.session.commit()
        return True

    def complete(self, session_id: UUID) -> bool:
        """Mark session as completed"""
        session_obj = self.get_by_id(session_id)
        if not session_obj:
            return False

        session_obj.status = "completed"
        session_obj.completed_at = datetime.utcnow()
        self.session.commit()
        return True

    def list_active(self, limit: int = 100, offset: int = 0) -> List[ResearchSessionORM]:
        """List active research sessions"""
        return (
            self.session.query(ResearchSessionORM)
            .filter_by(status="in_progress")
            .order_by(desc(ResearchSessionORM.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete(self, session_id: UUID) -> bool:
        """Delete research session"""
        session_obj = self.get_by_id(session_id)
        if not session_obj:
            return False

        self.session.delete(session_obj)
        self.session.commit()
        return True


def health_check(session: Session) -> Dict[str, Any]:
    """
    Database health check with pgvector extension verification.

    Optimized: Uses single query with multiple aggregates for faster execution.

    Returns:
        Health status dict with connection, extension, and table info
    """
    try:
        # Check basic connectivity
        session.execute(text("SELECT 1"))

        # Check pgvector extension
        result = session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        has_pgvector = result.scalar() is not None

        # Count records with optimized query
        # Use func.count() which is faster than .count()
        count_query = text("""
            SELECT
                (SELECT COUNT(*) FROM contents) as content_count,
                (SELECT COUNT(*) FROM authors) as author_count
        """)
        counts = session.execute(count_query).fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "pgvector": "enabled" if has_pgvector else "disabled",
            "content_count": counts[0] if counts else 0,
            "author_count": counts[1] if counts else 0,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
