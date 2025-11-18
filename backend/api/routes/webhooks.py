"""
API Routes for Webhook Management

CRUD endpoints for managing user webhook configurations.

Endpoints:
- POST /webhooks - Create new webhook
- GET /webhooks - List user's webhooks
- GET /webhooks/{webhook_id} - Get webhook details
- PUT /webhooks/{webhook_id} - Update webhook
- DELETE /webhooks/{webhook_id} - Delete webhook
- POST /webhooks/{webhook_id}/verify - Verify webhook URL
- POST /webhooks/{webhook_id}/test - Send test event
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from backend.auth.api_keys import require_api_key
from backend.db.connection import get_session
from backend.db.models import WebhookORM
from backend.webhooks.sender import WebhookSender

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ============================================================================
# Configuration
# ============================================================================

VALID_EVENTS = [
    "card.published",
    "card.cited",
    "token.transferred",
]


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateWebhookRequest(BaseModel):
    """Request model for creating webhook"""

    webhook_url: str = Field(..., description="Webhook URL to send events to")
    description: Optional[str] = Field(None, description="Optional description")
    events: List[str] = Field(..., description="Events to subscribe to")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    retry_enabled: bool = Field(True, description="Enable retry on failure")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")


class UpdateWebhookRequest(BaseModel):
    """Request model for updating webhook"""

    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    description: Optional[str] = Field(None, description="Description")
    events: Optional[List[str]] = Field(None, description="Events to subscribe to")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    is_active: Optional[bool] = Field(None, description="Active status")
    retry_enabled: Optional[bool] = Field(None, description="Enable retry")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Maximum retry attempts")


class WebhookResponse(BaseModel):
    """Response model for webhook"""

    id: str
    user_id: str
    webhook_url: str
    description: Optional[str]
    events: List[str]
    is_active: bool
    is_verified: bool
    custom_headers: Dict[str, str]
    total_deliveries: str
    successful_deliveries: str
    failed_deliveries: str
    last_delivery_at: Optional[str]
    last_delivery_status: Optional[str]
    retry_enabled: bool
    max_retries: str
    created_at: str
    updated_at: str
    verified_at: Optional[str]


class WebhookListResponse(BaseModel):
    """Response model for webhook list"""

    webhooks: List[WebhookResponse]
    total: int


class TestWebhookRequest(BaseModel):
    """Request model for testing webhook"""

    event_type: str = Field(..., description="Event type to test")
    payload: Optional[Dict] = Field(None, description="Optional test payload")


# ============================================================================
# Helper Functions
# ============================================================================


def validate_events(events: List[str]) -> None:
    """
    Validate event types.

    Args:
        events: List of event types to validate

    Raises:
        HTTPException: If any event is invalid
    """
    invalid_events = [e for e in events if e not in VALID_EVENTS]
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event types: {', '.join(invalid_events)}. "
            f"Valid events: {', '.join(VALID_EVENTS)}",
        )


def webhook_to_response(webhook: WebhookORM) -> WebhookResponse:
    """
    Convert webhook ORM to response model.

    Args:
        webhook: Webhook ORM object

    Returns:
        WebhookResponse object
    """
    return WebhookResponse(
        id=str(webhook.id),
        user_id=str(webhook.user_id),
        webhook_url=webhook.webhook_url,
        description=webhook.description,
        events=webhook.events,
        is_active=webhook.is_active,
        is_verified=webhook.is_verified,
        custom_headers=webhook.custom_headers or {},
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_delivery_at=webhook.last_delivery_at.isoformat() if webhook.last_delivery_at else None,
        last_delivery_status=webhook.last_delivery_status,
        retry_enabled=webhook.retry_enabled,
        max_retries=webhook.max_retries,
        created_at=webhook.created_at.isoformat(),
        updated_at=webhook.updated_at.isoformat(),
        verified_at=webhook.verified_at.isoformat() if webhook.verified_at else None,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    request: CreateWebhookRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Create new webhook configuration.

    Subscribes to specified events and sends HTTP POST to webhook URL when events occur.

    **Supported Events:**
    - `card.published`: When a card is published
    - `card.cited`: When a card receives an attribution
    - `token.transferred`: When tokens are transferred

    **Example:**
    ```json
    {
        "webhook_url": "https://example.com/webhook",
        "description": "Production webhook",
        "events": ["card.published", "card.cited"],
        "custom_headers": {
            "Authorization": "Bearer your-secret-token"
        },
        "retry_enabled": true,
        "max_retries": 3
    }
    ```
    """
    try:
        # Validate events
        validate_events(request.events)

        # Convert user_id to UUID
        user_uuid = UUID(user_id)

        # Create webhook
        webhook = WebhookORM(
            user_id=user_uuid,
            webhook_url=request.webhook_url,
            description=request.description,
            events=request.events,
            custom_headers=request.custom_headers or {},
            retry_enabled=request.retry_enabled,
            max_retries=str(request.max_retries),
        )

        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        return webhook_to_response(webhook)

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    user_id: str = Depends(require_api_key),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    """
    List user's webhooks.

    Returns all webhook configurations for the authenticated user.

    **Query Parameters:**
    - `is_active`: Filter by active status (true/false)
    - `event_type`: Filter by event type
    - `limit`: Maximum results (default: 100)
    - `offset`: Results offset (default: 0)
    """
    try:
        user_uuid = UUID(user_id)

        # Build query
        query = db.query(WebhookORM).filter(WebhookORM.user_id == user_uuid)

        if is_active is not None:
            query = query.filter(WebhookORM.is_active == is_active)

        if event_type:
            if event_type not in VALID_EVENTS:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
            query = query.filter(WebhookORM.events.contains([event_type]))

        # Get total count
        total = query.count()

        # Get paginated results
        webhooks = query.order_by(WebhookORM.created_at.desc()).offset(offset).limit(limit).all()

        return WebhookListResponse(
            webhooks=[webhook_to_response(wh) for wh in webhooks],
            total=total,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Get webhook details.

    Returns detailed information about a specific webhook.
    """
    try:
        user_uuid = UUID(user_id)
        webhook_uuid = UUID(webhook_id)

        webhook = (
            db.query(WebhookORM)
            .filter(WebhookORM.id == webhook_uuid, WebhookORM.user_id == user_uuid)
            .first()
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return webhook_to_response(webhook)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Update webhook configuration.

    Updates webhook settings. Only specified fields will be updated.

    **Example:**
    ```json
    {
        "is_active": false,
        "events": ["card.published"]
    }
    ```
    """
    try:
        user_uuid = UUID(user_id)
        webhook_uuid = UUID(webhook_id)

        webhook = (
            db.query(WebhookORM)
            .filter(WebhookORM.id == webhook_uuid, WebhookORM.user_id == user_uuid)
            .first()
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        # Update fields
        if request.webhook_url is not None:
            webhook.webhook_url = request.webhook_url
            webhook.is_verified = False  # Reset verification when URL changes

        if request.description is not None:
            webhook.description = request.description

        if request.events is not None:
            validate_events(request.events)
            webhook.events = request.events

        if request.custom_headers is not None:
            webhook.custom_headers = request.custom_headers

        if request.is_active is not None:
            webhook.is_active = request.is_active

        if request.retry_enabled is not None:
            webhook.retry_enabled = request.retry_enabled

        if request.max_retries is not None:
            webhook.max_retries = str(request.max_retries)

        webhook.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(webhook)

        return webhook_to_response(webhook)

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Delete webhook.

    Permanently removes webhook configuration.
    """
    try:
        user_uuid = UUID(user_id)
        webhook_uuid = UUID(webhook_id)

        webhook = (
            db.query(WebhookORM)
            .filter(WebhookORM.id == webhook_uuid, WebhookORM.user_id == user_uuid)
            .first()
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        db.delete(webhook)
        db.commit()

        return None

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.post("/{webhook_id}/verify")
async def verify_webhook(
    webhook_id: str,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Verify webhook URL.

    Sends a test ping to verify the webhook URL is reachable.

    **Test Payload:**
    ```json
    {
        "event": "webhook.ping",
        "timestamp": "2025-11-18T10:30:00",
        "webhook_id": "...",
        "message": "This is a test webhook delivery to verify your endpoint."
    }
    ```
    """
    try:
        user_uuid = UUID(user_id)
        webhook_uuid = UUID(webhook_id)

        webhook = (
            db.query(WebhookORM)
            .filter(WebhookORM.id == webhook_uuid, WebhookORM.user_id == user_uuid)
            .first()
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        sender = WebhookSender(db)
        result = await sender.verify_webhook(webhook_uuid)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify webhook: {str(e)}")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    request: TestWebhookRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Send test event to webhook.

    Triggers a test event delivery to the webhook URL.

    **Example:**
    ```json
    {
        "event_type": "card.published",
        "payload": {
            "card_id": "test-card-id",
            "title": "Test Card"
        }
    }
    ```
    """
    try:
        user_uuid = UUID(user_id)
        webhook_uuid = UUID(webhook_id)

        # Validate event type
        if request.event_type not in VALID_EVENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Valid events: {', '.join(VALID_EVENTS)}",
            )

        webhook = (
            db.query(WebhookORM)
            .filter(WebhookORM.id == webhook_uuid, WebhookORM.user_id == user_uuid)
            .first()
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        # Prepare test payload
        test_payload = request.payload or {
            "test": True,
            "message": "This is a test event",
        }

        sender = WebhookSender(db)
        result = await sender.send_event(
            event_type=request.event_type,
            user_id=user_uuid,
            payload=test_payload,
            webhook_id=webhook_uuid,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for webhook system.
    """
    return {
        "status": "healthy",
        "service": "webhook-system",
        "version": "1.0.0",
        "supported_events": VALID_EVENTS,
    }
