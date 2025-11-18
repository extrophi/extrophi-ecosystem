"""
Webhook ORM Model

Stores user-configured webhook URLs for event notifications.
Supports events: card.published, card.cited, token.transferred
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class WebhookORM(Base):
    """ORM model for webhook configurations"""

    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Webhook details
    webhook_url = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)

    # Event filtering
    events = Column(ARRAY(String), nullable=False, default=[])  # card.published, card.cited, token.transferred

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Headers for authentication (e.g., Authorization: Bearer token)
    custom_headers = Column(JSONB, nullable=True, default={})

    # Delivery tracking
    total_deliveries = Column(String(20), nullable=False, default="0")
    successful_deliveries = Column(String(20), nullable=False, default="0")
    failed_deliveries = Column(String(20), nullable=False, default="0")
    last_delivery_at = Column(DateTime, nullable=True)
    last_delivery_status = Column(String(50), nullable=True)  # success, failed, timeout

    # Retry configuration
    retry_enabled = Column(Boolean, nullable=False, default=True)
    max_retries = Column(String(10), nullable=False, default="3")

    # Metadata
    metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # Indices for performance
    __table_args__ = (
        Index("idx_webhooks_user_id", "user_id"),
        Index("idx_webhooks_is_active", "is_active"),
        Index("idx_webhooks_events", "events", postgresql_using="gin"),
        Index("idx_webhooks_user_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<WebhookORM(id={self.id}, user_id={self.user_id}, url={self.webhook_url})>"
