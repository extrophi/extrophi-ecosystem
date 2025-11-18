"""
Webhook Sender Module

Sends HTTP POST requests to configured webhook URLs when events occur.
Supports retry logic, delivery tracking, and event filtering.

Events:
- card.published: When a card is published
- card.cited: When a card receives an attribution (citation, remix, reply)
- token.transferred: When tokens are transferred between users
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from backend.db.models import WebhookORM

logger = logging.getLogger(__name__)


class WebhookSender:
    """
    Sends webhook notifications to configured URLs.

    Handles HTTP POST delivery, retries, and tracking.
    """

    def __init__(self, db: Session, timeout: int = 10):
        """
        Initialize webhook sender.

        Args:
            db: SQLAlchemy database session
            timeout: HTTP request timeout in seconds (default: 10)
        """
        self.db = db
        self.timeout = timeout

    async def send_event(
        self,
        event_type: str,
        user_id: UUID,
        payload: Dict[str, Any],
        webhook_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Send event to all configured webhooks for user.

        Args:
            event_type: Event type (card.published, card.cited, token.transferred)
            user_id: User ID to send webhooks for
            payload: Event payload data
            webhook_id: Optional specific webhook ID (send to only this webhook)

        Returns:
            Dict with delivery results
        """
        # Get webhooks for this user and event type
        query = self.db.query(WebhookORM).filter(
            WebhookORM.user_id == user_id,
            WebhookORM.is_active == True,
        )

        if webhook_id:
            query = query.filter(WebhookORM.id == webhook_id)

        webhooks = query.all()

        # Filter webhooks by event type
        webhooks = [wh for wh in webhooks if event_type in wh.events]

        if not webhooks:
            logger.info(f"No active webhooks configured for user {user_id} and event {event_type}")
            return {
                "event_type": event_type,
                "user_id": str(user_id),
                "webhooks_triggered": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
            }

        # Prepare event payload
        event_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "data": payload,
        }

        # Send to all webhooks
        results = []
        for webhook in webhooks:
            result = await self._deliver_webhook(webhook, event_payload)
            results.append(result)

        # Count successes and failures
        successful = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])

        return {
            "event_type": event_type,
            "user_id": str(user_id),
            "webhooks_triggered": len(webhooks),
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "results": results,
        }

    async def _deliver_webhook(
        self,
        webhook: WebhookORM,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deliver webhook to a single URL with retry logic.

        Args:
            webhook: Webhook ORM object
            payload: Event payload to send

        Returns:
            Dict with delivery result
        """
        max_retries = int(webhook.max_retries) if webhook.retry_enabled else 0
        attempt = 0
        last_error = None

        while attempt <= max_retries:
            try:
                # Send HTTP POST request
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        webhook.webhook_url,
                        json=payload,
                        headers=webhook.custom_headers or {},
                    )

                # Check if successful (2xx status code)
                if 200 <= response.status_code < 300:
                    # Update webhook delivery stats
                    webhook.total_deliveries = str(int(webhook.total_deliveries) + 1)
                    webhook.successful_deliveries = str(int(webhook.successful_deliveries) + 1)
                    webhook.last_delivery_at = datetime.utcnow()
                    webhook.last_delivery_status = "success"
                    self.db.commit()

                    logger.info(
                        f"Webhook delivered successfully: {webhook.id} to {webhook.webhook_url} "
                        f"(status: {response.status_code})"
                    )

                    return {
                        "webhook_id": str(webhook.id),
                        "webhook_url": webhook.webhook_url,
                        "success": True,
                        "status_code": response.status_code,
                        "attempts": attempt + 1,
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(
                        f"Webhook delivery failed: {webhook.id} to {webhook.webhook_url} "
                        f"(status: {response.status_code}, attempt: {attempt + 1}/{max_retries + 1})"
                    )

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(
                    f"Webhook delivery timeout: {webhook.id} to {webhook.webhook_url} "
                    f"(attempt: {attempt + 1}/{max_retries + 1})"
                )
            except httpx.RequestError as e:
                last_error = f"Request error: {str(e)}"
                logger.warning(
                    f"Webhook delivery error: {webhook.id} to {webhook.webhook_url} "
                    f"(error: {str(e)}, attempt: {attempt + 1}/{max_retries + 1})"
                )
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(
                    f"Unexpected webhook error: {webhook.id} to {webhook.webhook_url} "
                    f"(error: {str(e)}, attempt: {attempt + 1}/{max_retries + 1})"
                )

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                await asyncio.sleep(wait_time)

            attempt += 1

        # All retries failed
        webhook.total_deliveries = str(int(webhook.total_deliveries) + 1)
        webhook.failed_deliveries = str(int(webhook.failed_deliveries) + 1)
        webhook.last_delivery_at = datetime.utcnow()
        webhook.last_delivery_status = "failed"
        self.db.commit()

        logger.error(
            f"Webhook delivery failed after {max_retries + 1} attempts: "
            f"{webhook.id} to {webhook.webhook_url} (error: {last_error})"
        )

        return {
            "webhook_id": str(webhook.id),
            "webhook_url": webhook.webhook_url,
            "success": False,
            "error": last_error,
            "attempts": attempt,
        }

    async def verify_webhook(self, webhook_id: UUID) -> Dict[str, Any]:
        """
        Verify webhook URL by sending a test ping.

        Args:
            webhook_id: Webhook ID to verify

        Returns:
            Dict with verification result
        """
        webhook = self.db.query(WebhookORM).filter(WebhookORM.id == webhook_id).first()

        if not webhook:
            return {
                "success": False,
                "error": "Webhook not found",
            }

        # Send test ping
        test_payload = {
            "event": "webhook.ping",
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": str(webhook_id),
            "message": "This is a test webhook delivery to verify your endpoint.",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook.webhook_url,
                    json=test_payload,
                    headers=webhook.custom_headers or {},
                )

            if 200 <= response.status_code < 300:
                # Mark webhook as verified
                webhook.is_verified = True
                webhook.verified_at = datetime.utcnow()
                self.db.commit()

                logger.info(f"Webhook verified successfully: {webhook.id}")

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Webhook verified successfully",
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }
