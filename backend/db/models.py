"""SQLAlchemy ORM models and Pydantic schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================


class ContentORM(Base):
    """ORM model for unified content across all platforms"""

    __tablename__ = "contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform = Column(String(50), nullable=False)  # twitter, youtube, reddit, amazon, web
    source_url = Column(Text, unique=True, nullable=False, index=True)
    author_id = Column(String(255), nullable=False, index=True)
    content_title = Column(Text, nullable=True)
    content_body = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True, index=True)

    # Metrics stored as JSONB for flexibility
    metrics = Column(JSONB, nullable=True, default={})  # likes, views, retweets, engagement

    # LLM analysis results
    analysis = Column(JSONB, nullable=True, default={})  # frameworks, hooks, themes, patterns

    # Vector embedding for semantic search (1536 dims for OpenAI)
    embedding = Column(Vector(1536), nullable=True)

    # Metadata for platform-specific data
    metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    analyzed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key to author
    author = relationship("AuthorORM", back_populates="contents")

    # Indices for performance
    __table_args__ = (
        Index("idx_platform_author", "platform", "author_id"),
        Index("idx_platform_published", "platform", "published_at"),
        Index(
            "idx_embedding_ivfflat",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"op_class": "vector_cosine_ops"},
        ),
    )

    def __repr__(self):
        return f"<ContentORM(id={self.id}, platform={self.platform}, author_id={self.author_id})>"


class AuthorORM(Base):
    """ORM model for content authors/creators"""

    __tablename__ = "authors"

    id = Column(String(255), primary_key=True)  # platform_username or user_id
    platform = Column(String(50), nullable=False)  # twitter, youtube, reddit, etc.
    username = Column(String(255), nullable=False)
    display_name = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

    # Authority metrics
    follower_count = Column(String(20), nullable=True)  # Store as string to handle large numbers
    following_count = Column(String(20), nullable=True)
    content_count = Column(String(20), nullable=True)

    # Computed authority score
    authority_score = Column(String(10), nullable=True)  # 0.0-1.0

    # Links and metadata
    profile_url = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contents = relationship("ContentORM", back_populates="author", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_platform_username", "platform", "username"),
        Index("idx_authority_score", "authority_score"),
    )

    def __repr__(self):
        return f"<AuthorORM(id={self.id}, username={self.username}, platform={self.platform})>"


class PatternORM(Base):
    """ORM model for detected cross-platform patterns"""

    __tablename__ = "patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # elaboration, theme, hook, framework
    description = Column(Text, nullable=False)

    # References to content pieces
    content_ids = Column(JSONB, nullable=False, default=[])  # List of UUID strings

    # Similarity score
    confidence_score = Column(String(10), nullable=True)  # 0.0-1.0

    # Pattern details
    analysis = Column(JSONB, nullable=True, default={})

    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_author_pattern_type", "author_id", "pattern_type"),)

    def __repr__(self):
        return f"<PatternORM(id={self.id}, pattern_type={self.pattern_type})>"


class ResearchSessionORM(Base):
    """ORM model for tracking research sessions and queries"""

    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_name = Column(String(255), nullable=False)
    project_brief = Column(Text, nullable=True)

    # Session parameters
    target_authorities = Column(JSONB, nullable=True, default=[])
    platforms = Column(JSONB, nullable=True, default=[])
    keywords = Column(JSONB, nullable=True, default=[])

    # Results
    total_pieces_scraped = Column(String(20), default="0")
    total_pieces_analyzed = Column(String(20), default="0")
    patterns_detected = Column(String(20), default="0")

    # Generated outputs
    outputs = Column(JSONB, nullable=True, default={})  # course_script, briefs, etc.

    # Status
    status = Column(String(50), default="in_progress")  # in_progress, completed, failed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_session_status", "status"),
        Index("idx_session_created", "created_at"),
    )

    def __repr__(self):
        return f"<ResearchSessionORM(id={self.id}, name={self.session_name})>"


# ============================================================================
# Pydantic v2 Schemas
# ============================================================================


class AuthorModel(BaseModel):
    """Pydantic model for author information"""

    id: str
    platform: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    follower_count: Optional[str] = None
    following_count: Optional[str] = None
    content_count: Optional[str] = None
    authority_score: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ContentModel(BaseModel):
    """Pydantic model for content itself"""

    title: Optional[str] = None
    body: str
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    word_count: Optional[int] = None


class MetricsModel(BaseModel):
    """Pydantic model for engagement metrics"""

    likes: Optional[int] = None
    retweets: Optional[int] = None
    replies: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    engagement_rate: Optional[float] = None
    reach: Optional[int] = None
    impressions: Optional[int] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class AnalysisModel(BaseModel):
    """Pydantic model for LLM analysis results"""

    frameworks: List[str] = Field(default_factory=list)  # AIDA, PAS, BAB, PASTOR, etc.
    hooks: List[str] = Field(default_factory=list)  # Hook types found
    themes: List[str] = Field(default_factory=list)  # Main themes/topics
    pain_points: List[str] = Field(default_factory=list)  # Identified pain points
    desires: List[str] = Field(default_factory=list)  # Identified desires/benefits
    key_insights: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None  # positive, negative, neutral, mixed
    tone: Optional[str] = None  # professional, casual, humorous, etc.
    target_audience: Optional[str] = None
    call_to_action: Optional[str] = None
    custom_analysis: Dict[str, Any] = Field(default_factory=dict)


class UnifiedContent(BaseModel):
    """Complete unified content model for all platforms"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    platform: str  # twitter, youtube, reddit, amazon, web
    source_url: str
    author: AuthorModel
    content: ContentModel
    metrics: MetricsModel = Field(default_factory=MetricsModel)
    analysis: Optional[AnalysisModel] = None
    embedding: Optional[List[float]] = None  # 1536 dimensions for OpenAI
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class PatternModel(BaseModel):
    """Model for detected patterns"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    author_id: str
    pattern_type: str  # elaboration, theme, hook, framework
    description: str
    content_ids: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    analysis: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ResearchSessionModel(BaseModel):
    """Model for research sessions"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_name: str
    project_brief: Optional[str] = None
    target_authorities: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    total_pieces_scraped: str = "0"
    total_pieces_analyzed: str = "0"
    patterns_detected: str = "0"
    outputs: Dict[str, Any] = Field(default_factory=dict)
    status: str = "in_progress"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
