"""SQLAlchemy ORM models and Pydantic schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4, UUID as PyUUID

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
from sqlalchemy import DECIMAL, BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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
    extra_metadata = Column(JSONB, nullable=True, default={})

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
    extra_metadata = Column(JSONB, nullable=True, default={})

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


class APIKeyORM(Base):
    """ORM model for API keys with rate limiting"""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Key identification
    key_name = Column(String(255), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First 8-12 chars for identification
    key_hash = Column(String(255), nullable=False, unique=True)  # SHA-256 hash

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_revoked = Column(Boolean, nullable=False, default=False)

    # Rate limiting (1000 requests per hour by default)
    rate_limit_requests = Column(Integer, nullable=False, default=1000)
    rate_limit_window_seconds = Column(Integer, nullable=False, default=3600)  # 1 hour
    current_usage_count = Column(Integer, nullable=False, default=0)
    rate_limit_window_start = Column(DateTime, nullable=True)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    request_count = Column(BigInteger, nullable=False, default=0)  # Total requests all time

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    # Indices
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_key_prefix", "key_prefix"),
        Index("idx_api_keys_is_active", "is_active"),
        Index("idx_api_keys_is_revoked", "is_revoked"),
        Index("idx_api_keys_user_active", "user_id", "is_active"),
        Index("idx_api_keys_created_at", "created_at"),
        Index("idx_api_keys_last_used_at", "last_used_at"),
        Index("idx_api_keys_expires_at", "expires_at"),
    )

    def __repr__(self):
        return f"<APIKeyORM(id={self.id}, key_name={self.key_name}, user_id={self.user_id})>"


class UserORM(Base):
    """ORM model for user accounts with $EXTROPY token balances"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)

    # $EXTROPY token balance (DECIMAL for precise money handling)
    extropy_balance = Column(DECIMAL(20, 8), nullable=False, default=Decimal("0.00000000"))

    # API authentication
    api_key_hash = Column(String(255), nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    cards = relationship("CardORM", back_populates="user", cascade="all, delete-orphan")
    ledger_from = relationship(
        "ExtropyLedgerORM",
        foreign_keys="ExtropyLedgerORM.from_user_id",
        back_populates="from_user",
    )
    ledger_to = relationship(
        "ExtropyLedgerORM", foreign_keys="ExtropyLedgerORM.to_user_id", back_populates="to_user"
    )

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<UserORM(id={self.id}, username={self.username}, balance={self.extropy_balance})>"


class CardORM(Base):
    """ORM model for published content cards from Writer module"""

    __tablename__ = "cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Card content
    title = Column(String(1000), nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(ARRAY(Text), default=[])

    # Privacy level from Writer
    privacy_level = Column(String(50), nullable=False)

    # Card category from Writer
    category = Column(String(50), nullable=False)

    # Source information
    source_platform = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    parent_card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    related_card_ids = Column(ARRAY(UUID), default=[])

    # Publishing status
    is_published = Column(Boolean, default=False)
    published_url = Column(Text, nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserORM", back_populates="cards")
    content = relationship("ContentORM")
    ledger_entries = relationship("ExtropyLedgerORM", back_populates="card")

    __table_args__ = (
        Index("idx_cards_user_id", "user_id"),
        Index("idx_cards_privacy_level", "privacy_level"),
        Index("idx_cards_category", "category"),
        Index("idx_cards_is_published", "is_published"),
        Index("idx_cards_content_id", "content_id"),
        Index("idx_cards_parent_card_id", "parent_card_id"),
        Index("idx_cards_created_at", "created_at"),
        Index("idx_cards_published_at", "published_at"),
        Index("idx_cards_user_published", "user_id", "is_published"),
    )

    def __repr__(self):
        return f"<CardORM(id={self.id}, title={self.title[:50]}, user_id={self.user_id})>"


class ExtropyLedgerORM(Base):
    """ORM model for immutable $EXTROPY transaction log"""

    __tablename__ = "extropy_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Transaction participants
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Transaction details
    amount = Column(DECIMAL(20, 8), nullable=False)
    transaction_type = Column(String(50), nullable=False)

    # Related entities
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    attribution_id = Column(
        UUID(as_uuid=True), ForeignKey("attributions.id", ondelete="SET NULL"), nullable=True
    )

    # Balances after transaction (for audit trail)
    from_user_balance_after = Column(DECIMAL(20, 8), nullable=True)
    to_user_balance_after = Column(DECIMAL(20, 8), nullable=True)

    # Description
    description = Column(Text, nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Timestamp (immutable - no updates allowed)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    from_user = relationship("UserORM", foreign_keys=[from_user_id], back_populates="ledger_from")
    to_user = relationship("UserORM", foreign_keys=[to_user_id], back_populates="ledger_to")
    card = relationship("CardORM", back_populates="ledger_entries")

    __table_args__ = (
        Index("idx_extropy_ledger_from_user_id", "from_user_id"),
        Index("idx_extropy_ledger_to_user_id", "to_user_id"),
        Index("idx_extropy_ledger_transaction_type", "transaction_type"),
        Index("idx_extropy_ledger_card_id", "card_id"),
        Index("idx_extropy_ledger_attribution_id", "attribution_id"),
        Index("idx_extropy_ledger_created_at", "created_at"),
        Index("idx_extropy_ledger_from_user_created", "from_user_id", "created_at"),
        Index("idx_extropy_ledger_to_user_created", "to_user_id", "created_at"),
    )

    def __repr__(self):
        return f"<ExtropyLedgerORM(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class AttributionORM(Base):
    """ORM model for citations, remixes, and replies between cards"""

    __tablename__ = "attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Source and target cards
    source_card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    target_card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)

    # Attribution type
    attribution_type = Column(String(50), nullable=False)

    # Details
    context = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)

    # $EXTROPY transfer on attribution
    extropy_transferred = Column(DECIMAL(20, 8), default=Decimal("0.00000000"))

    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_attributions_source_card_id", "source_card_id"),
        Index("idx_attributions_target_card_id", "target_card_id"),
        Index("idx_attributions_attribution_type", "attribution_type"),
        Index("idx_attributions_created_at", "created_at"),
        Index("idx_attributions_source_type", "source_card_id", "attribution_type"),
        Index("idx_attributions_target_type", "target_card_id", "attribution_type"),
    )

    def __repr__(self):
        return f"<AttributionORM(id={self.id}, type={self.attribution_type})>"


class UltraLearningORM(Base):
    """ORM model for ultra learning formatted content"""

    __tablename__ = "ultra_learning"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Original content metadata
    title = Column(Text, nullable=False)
    link = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False)
    author_id = Column(String(255), nullable=False)

    # Ultra Learning structured data
    meta_subject = Column(Text, nullable=False)
    concepts = Column(ARRAY(Text), default=[])
    facts = Column(ARRAY(Text), default=[])
    procedures = Column(ARRAY(Text), default=[])

    # Processing metadata
    llm_model = Column(String(100), default="claude-haiku-4-20250514")
    tokens_used = Column(Integer, nullable=True)
    cost_cents = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ultra_learning_content_id", "content_id"),
        Index("idx_ultra_learning_meta_subject", "meta_subject"),
        Index("idx_ultra_learning_platform", "platform"),
        Index("idx_ultra_learning_author_id", "author_id"),
        Index("idx_ultra_learning_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<UltraLearningORM(id={self.id}, meta_subject={self.meta_subject}, content_id={self.content_id})>"


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
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

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
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

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


class UserModel(BaseModel):
    """Pydantic model for user accounts"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    extropy_balance: Decimal = Decimal("0.00000000")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CardModel(BaseModel):
    """Pydantic model for content cards"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str
    body: str
    tags: List[str] = Field(default_factory=list)
    privacy_level: str
    category: str
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    content_id: Optional[str] = None
    parent_card_id: Optional[str] = None
    related_card_ids: List[str] = Field(default_factory=list)
    is_published: bool = False
    published_url: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExtropyLedgerModel(BaseModel):
    """Pydantic model for $EXTROPY transaction ledger entries"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    amount: Decimal
    transaction_type: str
    card_id: Optional[str] = None
    attribution_id: Optional[str] = None
    from_user_balance_after: Optional[Decimal] = None
    to_user_balance_after: Optional[Decimal] = None
    description: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AttributionModel(BaseModel):
    """Pydantic model for card attributions"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_card_id: str
    target_card_id: str
    attribution_type: str
    context: Optional[str] = None
    excerpt: Optional[str] = None
    extropy_transferred: Decimal = Decimal("0.00000000")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class UltraLearningModel(BaseModel):
    """Pydantic model for ultra learning formatted content"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content_id: str
    title: str
    link: str
    platform: str
    author_id: str
    meta_subject: str
    concepts: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    llm_model: str = "claude-haiku-4-20250514"
    tokens_used: Optional[int] = None
    cost_cents: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# API Key Management Schemas
# ============================================================================


class APIKeyCreateRequest(BaseModel):
    """Request model for creating a new API key"""

    key_name: str
    expires_at: Optional[datetime] = None
    rate_limit_requests: Optional[int] = 1000
    rate_limit_window_seconds: Optional[int] = 3600


class APIKeyModel(BaseModel):
    """Pydantic model for API key (without sensitive data)"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    key_name: str
    key_prefix: str
    is_active: bool = True
    is_revoked: bool = False
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 3600
    current_usage_count: int = 0
    rate_limit_window_start: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    request_count: int = 0
    expires_at: Optional[datetime] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Response model for API key creation (includes full key once)"""

    id: str
    key_name: str
    key_prefix: str
    api_key: str  # Full key only returned once on creation
    expires_at: Optional[datetime] = None
    created_at: datetime


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys"""

    keys: List[APIKeyModel]
    total: int
