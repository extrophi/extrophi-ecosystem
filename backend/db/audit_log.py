"""
Audit Log ORM Model

Tracks all API calls for security, compliance, and debugging.

Features:
- Logs all API requests and responses
- Tracks user/API key for authenticated requests
- Records request parameters, headers, and body
- Captures response status and duration
- Indexed for fast querying by endpoint, user, timestamp
- Supports filtering and pagination

Table: audit_logs
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID as PyUUID
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.db.models import Base


class AuditLogORM(Base):
    """ORM model for API audit logs"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Request identification
    endpoint = Column(String(500), nullable=False, index=True)  # /api/scrape, /api/query, etc.
    method = Column(String(10), nullable=False, index=True)  # GET, POST, PUT, DELETE, etc.
    path = Column(Text, nullable=False)  # Full path with query params

    # User/API key tracking
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # User if authenticated
    api_key_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # API key if used
    api_key_prefix = Column(String(20), nullable=True)  # For quick identification

    # Request details
    request_headers = Column(JSONB, nullable=True, default={})  # Headers (sensitive ones filtered)
    request_params = Column(JSONB, nullable=True, default={})  # Query params
    request_body = Column(JSONB, nullable=True, default={})  # Request body (if JSON)

    # Response details
    response_status = Column(Integer, nullable=False, index=True)  # 200, 404, 500, etc.
    response_body = Column(JSONB, nullable=True, default={})  # Response body (if JSON, truncated if large)
    response_size_bytes = Column(BigInteger, nullable=True)  # Response size in bytes

    # Performance metrics
    duration_ms = Column(Integer, nullable=False)  # Request duration in milliseconds

    # Client information
    client_ip = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)  # User-Agent header

    # Metadata
    error_message = Column(Text, nullable=True)  # Error message if request failed
    metadata = Column(JSONB, nullable=True, default={})  # Additional context

    # Timestamp (immutable - no updates)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Composite indices for common queries
    __table_args__ = (
        Index("idx_audit_logs_endpoint", "endpoint"),
        Index("idx_audit_logs_method", "method"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_api_key_id", "api_key_id"),
        Index("idx_audit_logs_response_status", "response_status"),
        Index("idx_audit_logs_client_ip", "client_ip"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_user_created", "user_id", "created_at"),
        Index("idx_audit_logs_endpoint_created", "endpoint", "created_at"),
        Index("idx_audit_logs_status_created", "response_status", "created_at"),
        Index("idx_audit_logs_endpoint_status", "endpoint", "response_status"),
    )

    def __repr__(self):
        return f"<AuditLogORM(id={self.id}, endpoint={self.endpoint}, status={self.response_status})>"


# ============================================================================
# Pydantic Schemas
# ============================================================================


class AuditLogModel(BaseModel):
    """Pydantic model for audit log entries"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    endpoint: str
    method: str
    path: str
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None
    api_key_prefix: Optional[str] = None
    request_headers: Dict[str, Any] = Field(default_factory=dict)
    request_params: Dict[str, Any] = Field(default_factory=dict)
    request_body: Dict[str, Any] = Field(default_factory=dict)
    response_status: int
    response_body: Dict[str, Any] = Field(default_factory=dict)
    response_size_bytes: Optional[int] = None
    duration_ms: int
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response model for audit log listing"""

    logs: list[AuditLogModel]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogStatsResponse(BaseModel):
    """Response model for audit log statistics"""

    total_requests: int
    unique_users: int
    unique_endpoints: int
    average_duration_ms: float
    status_code_distribution: Dict[str, int]
    top_endpoints: list[Dict[str, Any]]
    error_rate: float
    requests_per_day: Dict[str, int]
