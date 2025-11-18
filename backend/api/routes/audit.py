"""
Audit Log Query API Routes

Provides endpoints to query and analyze audit logs.

Features:
- List audit logs with filtering and pagination
- Search by user, endpoint, status code, date range
- Get detailed statistics and analytics
- Export audit logs for compliance

Endpoints:
- GET /api/audit/logs - List audit logs
- GET /api/audit/logs/{log_id} - Get specific log
- GET /api/audit/stats - Get audit statistics
- GET /api/audit/export - Export audit logs (CSV/JSON)

Security:
- Requires API key authentication
- Rate limited per API key
"""

import math
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from backend.auth.api_keys import require_api_key
from backend.db.audit_log import (
    AuditLogListResponse,
    AuditLogModel,
    AuditLogORM,
    AuditLogStatsResponse,
)
from backend.db.connection import get_session

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    # Pagination
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page (max 500)"),
    # Filters
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint (exact match)"),
    method: Optional[str] = Query(None, description="Filter by HTTP method (GET, POST, etc.)"),
    status_code: Optional[int] = Query(None, description="Filter by response status code"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP address"),
    # Date range
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    # Sorting
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    # Authentication
    current_user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    List audit logs with filtering, pagination, and sorting.

    Supports filtering by:
    - User ID
    - Endpoint
    - HTTP method
    - Response status code
    - Client IP
    - Date range

    Returns paginated results with total count and page info.
    """
    # Build query conditions
    conditions = []

    if user_id:
        try:
            user_uuid = UUID(user_id)
            conditions.append(AuditLogORM.user_id == user_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format (must be UUID)",
            )

    if endpoint:
        conditions.append(AuditLogORM.endpoint == endpoint)

    if method:
        conditions.append(AuditLogORM.method == method.upper())

    if status_code:
        conditions.append(AuditLogORM.response_status == status_code)

    if client_ip:
        conditions.append(AuditLogORM.client_ip == client_ip)

    if start_date:
        conditions.append(AuditLogORM.created_at >= start_date)

    if end_date:
        conditions.append(AuditLogORM.created_at <= end_date)

    # Build query
    query = select(AuditLogORM)
    if conditions:
        query = query.where(and_(*conditions))

    # Apply sorting
    sort_column = getattr(AuditLogORM, sort_by, AuditLogORM.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Get total count
    count_query = select(func.count()).select_from(AuditLogORM)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = db.execute(count_query).scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = db.execute(query)
    audit_logs = result.scalars().all()

    # Convert to response models
    log_models = [
        AuditLogModel(
            id=str(log.id),
            endpoint=log.endpoint,
            method=log.method,
            path=log.path,
            user_id=str(log.user_id) if log.user_id else None,
            api_key_id=str(log.api_key_id) if log.api_key_id else None,
            api_key_prefix=log.api_key_prefix,
            request_headers=log.request_headers or {},
            request_params=log.request_params or {},
            request_body=log.request_body or {},
            response_status=log.response_status,
            response_body=log.response_body or {},
            response_size_bytes=log.response_size_bytes,
            duration_ms=log.duration_ms,
            client_ip=log.client_ip,
            user_agent=log.user_agent,
            error_message=log.error_message,
            metadata=log.metadata or {},
            created_at=log.created_at,
        )
        for log in audit_logs
    ]

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return AuditLogListResponse(
        logs=log_models,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/logs/{log_id}", response_model=AuditLogModel)
async def get_audit_log(
    log_id: str,
    current_user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Get a specific audit log by ID.

    Returns detailed information about a single audit log entry.
    """
    # Parse UUID
    try:
        log_uuid = UUID(log_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid log_id format (must be UUID)",
        )

    # Query log
    stmt = select(AuditLogORM).where(AuditLogORM.id == log_uuid)
    result = db.execute(stmt)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with ID {log_id} not found",
        )

    # Convert to response model
    return AuditLogModel(
        id=str(log.id),
        endpoint=log.endpoint,
        method=log.method,
        path=log.path,
        user_id=str(log.user_id) if log.user_id else None,
        api_key_id=str(log.api_key_id) if log.api_key_id else None,
        api_key_prefix=log.api_key_prefix,
        request_headers=log.request_headers or {},
        request_params=log.request_params or {},
        request_body=log.request_body or {},
        response_status=log.response_status,
        response_body=log.response_body or {},
        response_size_bytes=log.response_size_bytes,
        duration_ms=log.duration_ms,
        client_ip=log.client_ip,
        user_agent=log.user_agent,
        error_message=log.error_message,
        metadata=log.metadata or {},
        created_at=log.created_at,
    )


@router.get("/stats", response_model=AuditLogStatsResponse)
async def get_audit_stats(
    # Date range
    start_date: Optional[datetime] = Query(
        None, description="Stats start date (default: 30 days ago)"
    ),
    end_date: Optional[datetime] = Query(None, description="Stats end date (default: now)"),
    # Authentication
    current_user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Get audit log statistics and analytics.

    Returns:
    - Total requests
    - Unique users
    - Unique endpoints
    - Average duration
    - Status code distribution
    - Top endpoints by request count
    - Error rate
    - Requests per day
    """
    # Default to last 30 days if no date range specified
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Build base query with date filter
    base_conditions = [
        AuditLogORM.created_at >= start_date,
        AuditLogORM.created_at <= end_date,
    ]

    # Total requests
    total_requests = db.execute(
        select(func.count()).select_from(AuditLogORM).where(and_(*base_conditions))
    ).scalar()

    # Unique users
    unique_users = db.execute(
        select(func.count(func.distinct(AuditLogORM.user_id)))
        .select_from(AuditLogORM)
        .where(and_(*base_conditions))
    ).scalar()

    # Unique endpoints
    unique_endpoints = db.execute(
        select(func.count(func.distinct(AuditLogORM.endpoint)))
        .select_from(AuditLogORM)
        .where(and_(*base_conditions))
    ).scalar()

    # Average duration
    avg_duration = db.execute(
        select(func.avg(AuditLogORM.duration_ms))
        .select_from(AuditLogORM)
        .where(and_(*base_conditions))
    ).scalar()
    average_duration_ms = float(avg_duration) if avg_duration else 0.0

    # Status code distribution
    status_distribution_result = db.execute(
        select(AuditLogORM.response_status, func.count())
        .where(and_(*base_conditions))
        .group_by(AuditLogORM.response_status)
        .order_by(desc(func.count()))
    ).fetchall()
    status_code_distribution = {str(status): count for status, count in status_distribution_result}

    # Top endpoints
    top_endpoints_result = db.execute(
        select(AuditLogORM.endpoint, func.count().label("count"), func.avg(AuditLogORM.duration_ms).label("avg_duration"))
        .where(and_(*base_conditions))
        .group_by(AuditLogORM.endpoint)
        .order_by(desc(func.count()))
        .limit(10)
    ).fetchall()
    top_endpoints = [
        {
            "endpoint": endpoint,
            "count": count,
            "avg_duration_ms": float(avg_duration) if avg_duration else 0.0,
        }
        for endpoint, count, avg_duration in top_endpoints_result
    ]

    # Error rate (4xx and 5xx status codes)
    error_count = db.execute(
        select(func.count())
        .select_from(AuditLogORM)
        .where(
            and_(
                *base_conditions,
                AuditLogORM.response_status >= 400,
            )
        )
    ).scalar()
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

    # Requests per day
    requests_per_day_result = db.execute(
        select(func.date(AuditLogORM.created_at).label("date"), func.count().label("count"))
        .where(and_(*base_conditions))
        .group_by(func.date(AuditLogORM.created_at))
        .order_by(func.date(AuditLogORM.created_at))
    ).fetchall()
    requests_per_day = {str(date): count for date, count in requests_per_day_result}

    return AuditLogStatsResponse(
        total_requests=total_requests,
        unique_users=unique_users,
        unique_endpoints=unique_endpoints,
        average_duration_ms=average_duration_ms,
        status_code_distribution=status_code_distribution,
        top_endpoints=top_endpoints,
        error_rate=error_rate,
        requests_per_day=requests_per_day,
    )


@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=1, description="Delete logs older than this many days"),
    current_user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Delete audit logs older than specified number of days.

    This endpoint is for maintenance and compliance (e.g., GDPR data retention).
    Default: Delete logs older than 90 days.

    Returns the number of deleted logs.
    """
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Count logs to be deleted
    count_query = select(func.count()).select_from(AuditLogORM).where(
        AuditLogORM.created_at < cutoff_date
    )
    delete_count = db.execute(count_query).scalar()

    # Delete old logs
    delete_query = AuditLogORM.__table__.delete().where(AuditLogORM.created_at < cutoff_date)
    db.execute(delete_query)
    db.commit()

    return {
        "message": f"Deleted {delete_count} audit logs older than {days} days",
        "deleted_count": delete_count,
        "cutoff_date": cutoff_date.isoformat(),
    }
