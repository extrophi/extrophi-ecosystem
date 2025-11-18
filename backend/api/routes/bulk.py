"""
API Routes for Bulk Card Operations

Endpoints:
- POST /bulk/import - Import many cards (async)
- POST /bulk/export - Export many cards (async)
- POST /bulk/delete - Delete many cards (async)
- GET /bulk/status/{task_id} - Check bulk operation status
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.api_keys import require_api_key
from backend.db.connection import get_session
from backend.db.models import CardORM
from backend.queue.celery_app import celery_app

router = APIRouter(prefix="/bulk", tags=["bulk"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CardImportInput(BaseModel):
    """Input model for a single card to import"""

    title: str = Field(..., description="Card title", max_length=1000)
    body: str = Field(..., description="Card body content")
    category: str = Field(..., description="Card category (BUSINESS, IDEAS, etc.)")
    privacy_level: str = Field(..., description="Privacy level (BUSINESS, IDEAS, PERSONAL, etc.)")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    source_platform: Optional[str] = Field(None, description="Source platform if applicable")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    metadata: Optional[Dict] = Field(default=None, description="Optional metadata")


class BulkImportRequest(BaseModel):
    """Request model for bulk import operation"""

    cards: List[CardImportInput] = Field(..., description="List of cards to import (max 10000)")
    publish_business: bool = Field(
        default=True, description="Auto-publish cards with BUSINESS privacy level"
    )
    publish_ideas: bool = Field(default=True, description="Auto-publish cards with IDEAS privacy level")

    class Config:
        json_schema_extra = {
            "example": {
                "cards": [
                    {
                        "title": "How to Build Momentum",
                        "body": "The key to building momentum is...",
                        "category": "BUSINESS",
                        "privacy_level": "BUSINESS",
                        "tags": ["business", "growth"],
                    }
                ],
                "publish_business": True,
                "publish_ideas": True,
            }
        }


class BulkExportRequest(BaseModel):
    """Request model for bulk export operation"""

    card_ids: Optional[List[str]] = Field(
        None, description="Specific card IDs to export (if None, export all user cards)"
    )
    privacy_levels: Optional[List[str]] = Field(
        None, description="Filter by privacy levels (if None, export all)"
    )
    categories: Optional[List[str]] = Field(None, description="Filter by categories (if None, export all)")
    published_only: bool = Field(default=False, description="Export only published cards")
    format: str = Field(default="json", description="Export format (json, markdown, csv)")
    include_metadata: bool = Field(default=True, description="Include metadata in export")

    class Config:
        json_schema_extra = {
            "example": {
                "privacy_levels": ["BUSINESS", "IDEAS"],
                "format": "json",
                "include_metadata": True,
            }
        }


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operation"""

    card_ids: List[str] = Field(..., description="List of card IDs to delete (max 10000)")
    soft_delete: bool = Field(
        default=True,
        description="Soft delete (mark as deleted) vs hard delete (remove from database)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "card_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "soft_delete": True,
            }
        }


class BulkOperationResponse(BaseModel):
    """Response model for bulk operation (async task initiated)"""

    task_id: str = Field(..., description="Celery task ID for tracking")
    status: str = Field(..., description="Initial task status (PENDING, STARTED, etc.)")
    message: str = Field(..., description="Human-readable message")
    estimated_duration_seconds: Optional[int] = Field(
        None, description="Estimated completion time in seconds"
    )
    check_status_url: str = Field(..., description="URL to check operation status")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "PENDING",
                "message": "Bulk import initiated for 1000 cards",
                "estimated_duration_seconds": 120,
                "check_status_url": "/bulk/status/550e8400-e29b-41d4-a716-446655440000",
            }
        }


class BulkImportResult(BaseModel):
    """Result model for completed bulk import"""

    cards_imported: int = Field(..., description="Number of cards successfully imported")
    cards_failed: int = Field(..., description="Number of cards that failed to import")
    cards_published: int = Field(..., description="Number of cards auto-published")
    extropy_earned: str = Field(..., description="Total $EXTROPY tokens earned")
    errors: List[Dict] = Field(default_factory=list, description="List of errors encountered")
    duration_seconds: float = Field(..., description="Total operation duration")


class BulkExportResult(BaseModel):
    """Result model for completed bulk export"""

    cards_exported: int = Field(..., description="Number of cards exported")
    export_format: str = Field(..., description="Export format used")
    export_data: str = Field(..., description="Exported data (JSON, Markdown, or CSV)")
    file_size_bytes: int = Field(..., description="Size of exported data in bytes")
    duration_seconds: float = Field(..., description="Total operation duration")


class BulkDeleteResult(BaseModel):
    """Result model for completed bulk delete"""

    cards_deleted: int = Field(..., description="Number of cards successfully deleted")
    cards_failed: int = Field(..., description="Number of cards that failed to delete")
    soft_delete: bool = Field(..., description="Whether soft delete was used")
    errors: List[Dict] = Field(default_factory=list, description="List of errors encountered")
    duration_seconds: float = Field(..., description="Total operation duration")


class BulkStatusResponse(BaseModel):
    """Response model for bulk operation status check"""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)")
    progress: Optional[Dict] = Field(None, description="Progress information if available")
    result: Optional[Dict] = Field(None, description="Final result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[str] = Field(None, description="Task start timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")


# ============================================================================
# Helper Functions
# ============================================================================


def convert_to_markdown(card: CardORM) -> str:
    """
    Convert card ORM to markdown format.

    Args:
        card: Card ORM instance

    Returns:
        Markdown formatted content
    """
    markdown_lines = [
        f"# {card.title}",
        "",
        f"**Category:** {card.category}",
        f"**Privacy:** {card.privacy_level}",
        "",
    ]

    if card.tags:
        tags_str = ", ".join([f"`{tag}`" for tag in card.tags])
        markdown_lines.extend([f"**Tags:** {tags_str}", ""])

    if card.source_platform:
        markdown_lines.extend([f"**Source:** {card.source_platform}", ""])

    markdown_lines.extend([
        "---",
        "",
        card.body,
        "",
        f"---",
        f"*Created: {card.created_at.strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    return "\n".join(markdown_lines)


def generate_slug(text: str, max_length: int = 60) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Text to convert to slug
        max_length: Maximum slug length

    Returns:
        URL-safe slug string
    """
    slug = text.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    if not slug:
        slug = f"card-{uuid4().hex[:8]}"

    unique_suffix = uuid4().hex[:8]
    slug = f"{slug}-{unique_suffix}"

    return slug


def estimate_duration(operation: str, count: int) -> int:
    """
    Estimate operation duration in seconds.

    Args:
        operation: Operation type (import, export, delete)
        count: Number of items to process

    Returns:
        Estimated duration in seconds
    """
    # Rough estimates based on operation type
    rates = {
        "import": 0.1,  # 10 cards per second
        "export": 0.05,  # 20 cards per second
        "delete": 0.02,  # 50 cards per second
    }

    base_rate = rates.get(operation, 0.1)
    estimated = int(count * base_rate) + 5  # Add 5 second overhead

    return max(estimated, 1)  # Minimum 1 second


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/import", response_model=BulkOperationResponse)
async def bulk_import_cards(
    request: BulkImportRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Bulk import cards (async operation).

    Accepts a large batch of cards and imports them asynchronously using Celery.
    Cards can be auto-published based on privacy level settings.

    **Features:**
    - Import up to 10,000 cards per request
    - Auto-publish BUSINESS and IDEAS cards (configurable)
    - Award $EXTROPY tokens for published cards (1 token per card)
    - Async processing via Celery for large batches
    - Detailed error reporting for failed imports

    **Example Request:**
    ```json
    {
        "cards": [
            {
                "title": "How to Build Momentum",
                "body": "Content here...",
                "category": "BUSINESS",
                "privacy_level": "BUSINESS",
                "tags": ["business", "growth"]
            }
        ],
        "publish_business": true,
        "publish_ideas": true
    }
    ```

    **Returns:**
    - `task_id`: Celery task ID for tracking progress
    - `check_status_url`: URL to check operation status
    - `estimated_duration_seconds`: Estimated completion time
    """
    try:
        # Validate request
        if len(request.cards) == 0:
            raise HTTPException(status_code=400, detail="No cards provided for import")

        if len(request.cards) > 10000:
            raise HTTPException(
                status_code=400, detail="Maximum 10,000 cards per import operation"
            )

        # Convert user_id to UUID
        user_uuid = UUID(user_id)

        # Import tasks module here to avoid circular imports
        from backend.tasks.bulk_operations import bulk_import_task

        # Prepare task data
        cards_data = [card.model_dump() for card in request.cards]

        # Launch async task
        task = bulk_import_task.delay(
            user_id=str(user_uuid),
            cards_data=cards_data,
            publish_business=request.publish_business,
            publish_ideas=request.publish_ideas,
        )

        # Estimate duration
        estimated_duration = estimate_duration("import", len(request.cards))

        return BulkOperationResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Bulk import initiated for {len(request.cards)} cards",
            estimated_duration_seconds=estimated_duration,
            check_status_url=f"/bulk/status/{task.id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate bulk import: {str(e)}")


@router.post("/export", response_model=BulkOperationResponse)
async def bulk_export_cards(
    request: BulkExportRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Bulk export cards (async operation).

    Exports cards to JSON, Markdown, or CSV format based on filters.

    **Features:**
    - Export all cards or specific card IDs
    - Filter by privacy level, category, or published status
    - Multiple export formats (JSON, Markdown, CSV)
    - Async processing for large exports
    - Include/exclude metadata

    **Export Formats:**
    - `json`: Structured JSON array of cards
    - `markdown`: Individual markdown files concatenated
    - `csv`: Tabular format with title, body, category, tags, etc.

    **Example Request:**
    ```json
    {
        "privacy_levels": ["BUSINESS", "IDEAS"],
        "format": "json",
        "include_metadata": true
    }
    ```

    **Returns:**
    - `task_id`: Celery task ID for tracking progress
    - `check_status_url`: URL to check operation status and retrieve export
    """
    try:
        # Convert user_id to UUID
        user_uuid = UUID(user_id)

        # Validate format
        valid_formats = ["json", "markdown", "csv"]
        if request.format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            )

        # Import tasks module here to avoid circular imports
        from backend.tasks.bulk_operations import bulk_export_task

        # Prepare task data
        task = bulk_export_task.delay(
            user_id=str(user_uuid),
            card_ids=request.card_ids,
            privacy_levels=request.privacy_levels,
            categories=request.categories,
            published_only=request.published_only,
            export_format=request.format,
            include_metadata=request.include_metadata,
        )

        return BulkOperationResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Bulk export initiated in {request.format} format",
            estimated_duration_seconds=30,  # Will be updated based on actual count
            check_status_url=f"/bulk/status/{task.id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate bulk export: {str(e)}")


@router.post("/delete", response_model=BulkOperationResponse)
async def bulk_delete_cards(
    request: BulkDeleteRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Bulk delete cards (async operation).

    Deletes multiple cards in a single operation. Supports both soft delete
    (mark as deleted) and hard delete (remove from database).

    **Features:**
    - Delete up to 10,000 cards per request
    - Soft delete (default) or hard delete
    - User authorization check (can only delete own cards)
    - Async processing via Celery
    - Detailed error reporting

    **Soft Delete vs Hard Delete:**
    - **Soft Delete** (recommended): Marks cards as deleted but keeps data
    - **Hard Delete**: Permanently removes cards from database (cannot be undone)

    **Example Request:**
    ```json
    {
        "card_ids": [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        ],
        "soft_delete": true
    }
    ```

    **Returns:**
    - `task_id`: Celery task ID for tracking progress
    - `check_status_url`: URL to check operation status
    """
    try:
        # Validate request
        if len(request.card_ids) == 0:
            raise HTTPException(status_code=400, detail="No card IDs provided for deletion")

        if len(request.card_ids) > 10000:
            raise HTTPException(
                status_code=400, detail="Maximum 10,000 cards per delete operation"
            )

        # Convert user_id to UUID
        user_uuid = UUID(user_id)

        # Import tasks module here to avoid circular imports
        from backend.tasks.bulk_operations import bulk_delete_task

        # Launch async task
        task = bulk_delete_task.delay(
            user_id=str(user_uuid),
            card_ids=request.card_ids,
            soft_delete=request.soft_delete,
        )

        # Estimate duration
        estimated_duration = estimate_duration("delete", len(request.card_ids))

        return BulkOperationResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Bulk delete initiated for {len(request.card_ids)} cards",
            estimated_duration_seconds=estimated_duration,
            check_status_url=f"/bulk/status/{task.id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate bulk delete: {str(e)}")


@router.get("/status/{task_id}", response_model=BulkStatusResponse)
async def get_bulk_operation_status(task_id: str):
    """
    Check status of a bulk operation.

    Returns the current status, progress, and results (if completed) of a bulk operation.

    **Task States:**
    - `PENDING`: Task is waiting to be executed
    - `STARTED`: Task is currently running
    - `SUCCESS`: Task completed successfully
    - `FAILURE`: Task failed with an error
    - `RETRY`: Task failed but is being retried

    **Example Response (In Progress):**
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "STARTED",
        "progress": {
            "current": 500,
            "total": 1000,
            "percent": 50
        }
    }
    ```

    **Example Response (Completed):**
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "SUCCESS",
        "result": {
            "cards_imported": 1000,
            "cards_failed": 0,
            "cards_published": 800,
            "extropy_earned": "800.00000000",
            "duration_seconds": 45.2
        },
        "completed_at": "2025-11-18T12:34:56Z"
    }
    ```
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)

        response = BulkStatusResponse(
            task_id=task_id,
            status=task_result.state,
        )

        # Add progress info if available
        if task_result.state == "STARTED" and task_result.info:
            response.progress = task_result.info

        # Add result if completed
        if task_result.state == "SUCCESS":
            response.result = task_result.result
            response.completed_at = datetime.utcnow().isoformat()

        # Add error if failed
        if task_result.state == "FAILURE":
            response.error = str(task_result.info)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve task status: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for bulk operations service.

    Returns basic system status including Celery worker availability.
    """
    try:
        # Check if Celery workers are available
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()

        worker_status = "healthy" if active_workers else "no_workers"

        return {
            "status": "healthy",
            "service": "bulk-operations",
            "version": "1.0.0",
            "celery_workers": worker_status,
            "worker_count": len(active_workers) if active_workers else 0,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "bulk-operations",
            "version": "1.0.0",
            "error": str(e),
        }
